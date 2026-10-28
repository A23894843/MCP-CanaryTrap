"""FastAPI reporting API and minimal browser dashboard."""
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Request, Depends
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import hmac
import os
import re
import json
import httpx
from urllib.parse import urlsplit
from .harness import DemoHarness
from .storage import Store
from .http_gateway import router as http_gateway_router
from .gateway_core import load_http_upstreams
from .security_center import router as security_center_router, _actor_context, _require
from .gateway_core import validate_upstream_url

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "")

app = FastAPI(title="MCP-CanaryTrap", version="1.3.0",
              description="MCP decoy monitoring prototype with stdio and Streamable HTTP gateway adapters.")
app.include_router(http_gateway_router)
app.include_router(security_center_router)


@app.middleware("http")
async def security_and_production_auth(request: Request, call_next):
    """Add baseline security headers and protect every non-health route in production.

    Basic authentication is intentionally a minimal deployment guard. Put the service
    behind HTTPS and a managed identity provider for enterprise deployments.
    """
    path = request.url.path
    if APP_ENV == "production" and path not in {"/health", "/ready"}:
        if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
            response = JSONResponse(
                status_code=503,
                content={"detail": "Production authentication is not configured. Set DASHBOARD_USERNAME and DASHBOARD_PASSWORD."},
            )
            response.headers["WWW-Authenticate"] = 'Basic realm="MCP-CanaryTrap"'
        else:
            auth = request.headers.get("authorization", "")
            valid = False
            if auth.startswith("Basic "):
                import base64
                try:
                    decoded = base64.b64decode(auth[6:], validate=True).decode("utf-8")
                    username, password = decoded.split(":", 1)
                    valid = hmac.compare_digest(username, DASHBOARD_USERNAME) and hmac.compare_digest(password, DASHBOARD_PASSWORD)
                except (ValueError, UnicodeDecodeError):
                    valid = False
            if not valid:
                response = JSONResponse(status_code=401, content={"detail": "Authentication required"})
                response.headers["WWW-Authenticate"] = 'Basic realm="MCP-CanaryTrap"'
            else:
                response = await call_next(request)
    else:
        response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")
    if APP_ENV == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response
store = Store()
harness = DemoHarness(store)
TEMPLATE = Path(__file__).parent / "templates" / "index.html"


class CustomInteraction(BaseModel):
    """One examiner-supplied interaction; decoy status is never client supplied."""
    operation: str = Field(min_length=1, max_length=80)
    target: str = Field(min_length=1, max_length=250)
    target_kind: str = Field(default="other", max_length=30)
    details: str = Field(default="", max_length=500)


class CustomTestRequest(BaseModel):
    """Structured custom test submitted from the dashboard or API."""
    case_name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    decoy_targets: list[str] = Field(default_factory=list, max_length=100)
    interactions: list[CustomInteraction] = Field(min_length=1, max_length=100)

class HTTPGatewayConnectionRequest(BaseModel):
    """Non-secret HTTP gateway configuration submitted from the operator dashboard."""
    connection_id: str = Field(min_length=1, max_length=64)
    url: str = Field(min_length=8, max_length=2000)
    token_env: str = Field(default="", max_length=128)
    decoy_tools: list[str] = Field(default_factory=list, max_length=100)
    decoy_resources: list[str] = Field(default_factory=list, max_length=100)
    decoy_prompts: list[str] = Field(default_factory=list, max_length=100)

@app.get("/", response_class=HTMLResponse, tags=["dashboard"])
def dashboard() -> str:
    """Serve the static dashboard HTML."""
    return TEMPLATE.read_text(encoding="utf-8")

@app.get("/health", tags=["system"])
def health() -> dict:
    """Public liveness endpoint; deliberately contains no secret/config values."""
    return {"status": "ok", "service": "MCP-CanaryTrap", "mode": "simulation+MCP-gateway", "environment": APP_ENV}


@app.get("/ready", tags=["system"])
def readiness() -> dict:
    """Deployment readiness snapshot. This checks local configuration, not MCP reachability."""
    production_auth_configured = bool(DASHBOARD_USERNAME and DASHBOARD_PASSWORD)
    checks = {
        "database_path_configured": bool(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")),
        "production_auth_configured": production_auth_configured if APP_ENV == "production" else None,
        "production_mode": APP_ENV == "production",
        "live_mcp_monitoring": True,
        "http_gateway_configured": bool(os.getenv("CANARYTRAP_HTTP_UPSTREAMS", "{}").strip() not in {"", "{}"}),
        "stdio_gateway": "available as a local MCP stdio proxy command",
        "persistent_database_backend": "sqlite",
    }
    ready = APP_ENV != "production" or production_auth_configured
    return {"ready": ready, "service": "MCP-CanaryTrap", "checks": checks,
            "note": "Readiness checks configuration only; run end-to-end transport tests before production use."}

@app.post("/api/gateway/connections", tags=["live MCP gateway"])
def save_gateway_connection(request: HTTPGatewayConnectionRequest, ctx=Depends(_actor_context)) -> dict:
    """Save non-secret HTTP upstream settings to the local persistent configuration store."""
    _require(ctx, {"admin", "operator"})
    connection_id = request.connection_id.strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", connection_id):
        raise HTTPException(status_code=422, detail="Connection ID may contain letters, numbers, underscores, and hyphens only")
    url = request.url.strip()
    parsed_url = urlsplit(url)
    if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname:
        raise HTTPException(status_code=422, detail="Upstream URL must be a valid http:// or https:// URL")
    if parsed_url.username or parsed_url.password:
        raise HTTPException(status_code=422, detail="Do not embed username/password credentials in the upstream URL")
    try:
        validate_upstream_url(url)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    token_env = request.token_env.strip()
    if token_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env):
        raise HTTPException(status_code=422, detail="token_env must be a valid environment-variable name")
    if token_env and APP_ENV == "production" and parsed_url.scheme != "https":
        raise HTTPException(status_code=422, detail="Use an HTTPS upstream URL when configuring a bearer token in production")
    decoys = {
        "decoy_tools": [x.strip() for x in request.decoy_tools if x.strip()],
        "decoy_resources": [x.strip() for x in request.decoy_resources if x.strip()],
        "decoy_prompts": [x.strip() for x in request.decoy_prompts if x.strip()],
    }
    if not any(decoys.values()):
        raise HTTPException(status_code=422, detail="Configure at least one decoy tool, resource, or prompt")
    for kind, values in decoys.items():
        if len(values) != len(set(values)):
            raise HTTPException(status_code=422, detail=f"Duplicate values in {kind}")
        if any(len(value) > 250 for value in values):
            raise HTTPException(status_code=422, detail=f"Values in {kind} must be 250 characters or fewer")
    connection = {"id": connection_id, "url": url, "token_env": token_env, **decoys}
    store.save_gateway_connection(connection)
    return {
        "saved": True,
        "connection": {
            "id": connection_id, "url": url, "token_env": token_env,
            **decoys, "token_configured": bool(token_env and os.getenv(token_env, "")),
            "endpoint": f"/gateway/{connection_id}",
        },
        "secrets_stored": False,
        "note": "Configuration is active immediately. If token_env is set, add that secret to the server environment before connecting."
    }


@app.delete("/api/gateway/connections/{connection_id}", tags=["live MCP gateway"])
def delete_gateway_connection(connection_id: str, ctx=Depends(_actor_context)) -> dict:
    """Delete a dashboard-saved connection; environment-defined connections remain active."""
    _require(ctx, {"admin"})
    deleted = store.delete_gateway_connection(connection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="No dashboard-saved connection with that ID")
    return {"deleted": True, "connection_id": connection_id}


@app.post("/api/gateway/connections/{connection_id}/test", tags=["live MCP gateway"])
async def test_gateway_connection(connection_id: str, ctx=Depends(_actor_context)) -> dict:
    """Send an MCP initialize request to verify reachability and protocol response."""
    _require(ctx, {"admin", "operator"})
    try:
        config = load_http_upstreams().get(connection_id)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not config:
        raise HTTPException(status_code=404, detail="Connection is not configured")
    headers = {"accept": "application/json, text/event-stream", "content-type": "application/json"}
    token_env = str(config.get("token_env") or "")
    if token_env:
        token = os.getenv(token_env, "")
        if not token:
            raise HTTPException(status_code=503, detail=f"Configured credential environment variable '{token_env}' is not set")
        headers["authorization"] = f"Bearer {token}"
    payload = {"jsonrpc": "2.0", "id": "canarytrap-init-check", "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "MCP-CanaryTrap", "version": "1.3.0"}
    }}
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=5.0), follow_redirects=False) as client:
            response = await client.post(config["url"], json=payload, headers=headers)
            if response.status_code >= 400:
                raise HTTPException(status_code=502, detail=f"Upstream returned HTTP {response.status_code}")
            result_payload = None
            if "application/json" in response.headers.get("content-type", ""):
                try:
                    result_payload = response.json()
                except ValueError:
                    result_payload = None
            elif "text/event-stream" in response.headers.get("content-type", ""):
                for line in response.text.splitlines():
                    if line.startswith("data:"):
                        try:
                            result_payload = json.loads(line[5:].strip())
                            break
                        except json.JSONDecodeError:
                            continue
            result = result_payload.get("result") if isinstance(result_payload, dict) else None
            if not isinstance(result, dict) or not result.get("protocolVersion"):
                raise HTTPException(status_code=502, detail="Upstream did not return a valid MCP initialize result")
            session_id = response.headers.get("mcp-session-id")
            if session_id:
                session_headers = {**headers, "mcp-session-id": session_id, "mcp-protocol-version": result.get("protocolVersion", "2025-03-26")}
                try:
                    await client.post(config["url"], json={"jsonrpc": "2.0", "method": "notifications/initialized"}, headers=session_headers)
                    await client.delete(config["url"], headers=session_headers)
                except httpx.HTTPError:
                    pass
            server_info = result.get("serverInfo") if isinstance(result.get("serverInfo"), dict) else {}
            return {"connected": True, "connection_id": connection_id,
                    "protocol_version": result.get("protocolVersion"),
                    "server_name": server_info.get("name", "unknown"),
                    "server_version": server_info.get("version", "unknown"),
                    "note": "Initialize handshake succeeded. This is a connectivity check, not a security certification."}
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Upstream MCP initialize timed out") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Could not connect to upstream MCP server: {type(exc).__name__}") from exc


@app.get("/api/gateway/config", tags=["live MCP gateway"])
def gateway_config_status(ctx=Depends(_actor_context)) -> dict:
    """Return non-secret gateway configuration status for the dashboard."""
    _require(ctx, {"admin", "operator"})
    try:
        upstreams = load_http_upstreams()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "http_connections": [
            {"id": connection_id, "url": cfg["url"],
             "decoy_tools": len(cfg["decoy_tools"]),
             "decoy_resources": len(cfg["decoy_resources"]),
             "decoy_prompts": len(cfg["decoy_prompts"]),
             "token_configured": bool(cfg["token_env"] and os.getenv(str(cfg["token_env"]), ""))}
            for connection_id, cfg in upstreams.items()
        ],
        "stdio_proxy_available": True,
        "secrets_returned": False,
        "note": "This reports configured adapters only; it does not prove upstream connectivity or certify production readiness."
    }


@app.get("/api/sessions", tags=["sessions"])
def sessions(ctx=Depends(_actor_context)) -> list[dict]:
    """List persisted test sessions for the authenticated tenant."""
    return store.list_sessions(tenant=ctx["tenant"])

@app.get("/api/events", tags=["events"])
def events(session_id: str | None = Query(default=None), ctx=Depends(_actor_context)) -> list[dict]:
    """List recent events restricted to the authenticated tenant."""
    return store.list_events(session_id, tenant=ctx["tenant"])

@app.post("/api/demo/{scenario}", tags=["demo"])
def run_demo(scenario: str, ctx=Depends(_actor_context)) -> dict:
    """Run a benign or overreaching simulation in the authenticated tenant."""
    if scenario not in {"benign", "overreaching"}:
        raise HTTPException(status_code=400, detail="scenario must be benign or overreaching")
    return harness.run(scenario, tenant=ctx["tenant"])


@app.post("/api/custom-test", tags=["custom tests"])
def run_custom_test(request: CustomTestRequest, ctx=Depends(_actor_context)) -> dict:
    """Evaluate a user-defined case within the authenticated tenant."""
    decoys = [target.strip() for target in request.decoy_targets if target.strip()]
    if len({target.casefold() for target in decoys}) != len(decoys):
        raise HTTPException(status_code=422, detail="decoy targets must be unique (case-insensitive)")
    try:
        return harness.run_custom(
            case_name=request.case_name,
            description=request.description,
            decoy_targets=decoys,
            interactions=[item.model_dump() for item in request.interactions],
            tenant=ctx["tenant"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

def run() -> None:
    """Start the server; hosted platforms supply HOST/PORT through environment variables."""
    host = os.getenv("HOST", "127.0.0.1" if APP_ENV != "production" else "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("mcp_canarytrap.api:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    run()
