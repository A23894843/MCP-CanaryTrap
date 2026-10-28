"""HTTP Streamable MCP reverse-proxy routes for CanaryTrap.

Configure approved upstreams using CANARYTRAP_HTTP_UPSTREAMS. Secrets are referenced
by environment-variable name (token_env), never submitted through the dashboard.
"""
from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.background import BackgroundTask

from .gateway_core import GatewayRecorder, decoy_kind, inject_decoys, load_http_upstreams, request_operation, synthetic_response, transform_response
from .security_center import policy_decision, resolve_gateway_tenant

router = APIRouter(tags=["live MCP gateway"])
_HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "content-length", "host"}


def _headers_for_upstream(request: Request, config: dict[str, Any]) -> dict[str, str]:
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP and k.lower() != "authorization" and k.lower() != "x-canarytrap-api-key"}
    token_env = str(config.get("token_env") or "").strip()
    if token_env:
        token = os.getenv(token_env, "")
        if not token:
            raise HTTPException(status_code=503, detail=f"Configured credential environment variable '{token_env}' is not set")
        if os.getenv("APP_ENV", "development").strip().lower() == "production" and not str(config["url"]).startswith("https://"):
            raise HTTPException(status_code=422, detail="Use an HTTPS upstream URL when forwarding a bearer token in production")
        headers["authorization"] = f"Bearer {token}"
    # Do not forward the dashboard/client Authorization header upstream: it may be
    # the CanaryTrap gateway credential rather than the upstream server credential.
    return headers


def _mutate_rpc(payload: Any, config: dict[str, Any], recorder: GatewayRecorder | None = None) -> Any:
    if isinstance(payload, list):
        return [_mutate_rpc(item, config, recorder) for item in payload]
    if not isinstance(payload, dict):
        return payload
    # The marker is attached by the request ID map in the caller when response method is known.
    return inject_decoys(payload, config)


async def _close_upstream(upstream_response: httpx.Response, client: httpx.AsyncClient) -> None:
    await upstream_response.aclose()
    await client.aclose()


def _transform_sse_frame(frame: bytes, config: dict[str, Any], request_methods: dict[str, str]) -> bytes:
    try:
        text = frame.decode("utf-8")
    except UnicodeDecodeError:
        return frame + b"\n\n"
    lines = text.splitlines()
    data_lines = [line[5:].lstrip() for line in lines if line.startswith("data:")]
    if not data_lines:
        return frame + b"\n\n"
    try:
        payload = json.loads("\n".join(data_lines))
        payload = transform_response(payload, request_methods, config)
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        lines = [line for line in lines if not line.startswith("data:")] + ["data: " + encoded]
        return ("\n".join(lines) + "\n\n").encode("utf-8")
    except (json.JSONDecodeError, TypeError):
        return frame + b"\n\n"


async def _stream_sse(content, config: dict[str, Any], request_methods: dict[str, str]):
    """Stream SSE frames while transforming complete JSON-RPC data messages."""
    buffer = b""
    async for chunk in content:
        buffer += chunk
        while True:
            # Accept both common SSE line endings.
            lf = buffer.find(b"\n\n")
            crlf = buffer.find(b"\r\n\r\n")
            candidates = [(idx, sep) for idx, sep in ((lf, b"\n\n"), (crlf, b"\r\n\r\n")) if idx >= 0]
            if not candidates:
                break
            idx, sep = min(candidates, key=lambda item: item[0])
            frame, buffer = buffer[:idx], buffer[idx + len(sep):]
            yield _transform_sse_frame(frame, config, request_methods)
        if len(buffer) > 1024 * 1024:
            # Bound memory if an upstream violates SSE framing.
            yield buffer
            buffer = b""
    if buffer:
        yield _transform_sse_frame(buffer, config, request_methods)


async def _proxy(request: Request, connection_id: str) -> Response:
    try:
        upstreams = load_http_upstreams()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    config = upstreams.get(connection_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"No approved HTTP MCP upstream named '{connection_id}' is configured")
    tenant = resolve_gateway_tenant(request.headers.get("x-canarytrap-api-key"))

    max_body_bytes = int(os.getenv("CANARYTRAP_MAX_REQUEST_BYTES", str(2 * 1024 * 1024)))
    content_length = request.headers.get("content-length", "")
    if content_length.isdigit() and int(content_length) > max_body_bytes:
        raise HTTPException(status_code=413, detail=f"MCP request exceeds configured limit ({max_body_bytes} bytes)")
    body = await request.body()
    if len(body) > max_body_bytes:
        raise HTTPException(status_code=413, detail=f"MCP request exceeds configured limit ({max_body_bytes} bytes)")
    message: Any = None
    request_methods: dict[str, str] = {}
    if request.method == "POST" and body:
        try:
            message = json.loads(body)
        except json.JSONDecodeError:
            message = None
        if isinstance(message, list):
            raise HTTPException(status_code=400, detail="JSON-RPC batch requests are not supported by the current CanaryTrap monitoring adapter")

    recorder: GatewayRecorder | None = None
    if request.method == "POST" and isinstance(message, dict):
        operation = request_operation(message)
        if operation:
            op, target, kind = operation
            actual_kind = decoy_kind(target, config, kind)
            recorder = GatewayRecorder(connection_id, request.headers.get("mcp-session-id") and ("gw-" + connection_id + "-" + request.headers["mcp-session-id"]), tenant=tenant)
            decision = policy_decision(op, target, kind, tenant)
            recorder.record(op, target[:250], kind, actual_kind == kind, f"HTTP MCP request observed; policy={decision['action']}; arguments omitted", policy_action=decision["action"])
            if decision["action"] == "deny":
                if message.get("id") is None:
                    return Response(status_code=202, headers={"MCP-CanaryTrap-Policy": "denied"})
                denied = {"jsonrpc":"2.0","id":message.get("id"),"error":{"code":-32001,"message":"Blocked by MCP-CanaryTrap policy","data":{"rule_id":decision.get("rule_id"),"rule_name":decision.get("rule_name")}}}
                return JSONResponse(denied, headers={"MCP-CanaryTrap-Policy": "denied"})
            if actual_kind == kind:
                result = synthetic_response(message, kind, target)
                if result is None:
                    return Response(status_code=202)
                return JSONResponse(result, headers={"MCP-CanaryTrap-Event": "decoy-interaction-recorded"})
        if message.get("method") and message.get("id") is not None:
            request_methods[str(message["id"])] = str(message["method"])

    upstream_url = config["url"]
    # Optional path suffix lets clients use /gateway/<id>/<endpoint-suffix> when required.
    route_suffix = request.path_params.get("rest", "")
    if route_suffix:
        upstream_url = upstream_url.rstrip("/") + "/" + route_suffix.lstrip("/")
    headers = _headers_for_upstream(request, config)
    default_timeout = float(os.getenv("CANARYTRAP_UPSTREAM_TIMEOUT", "60"))
    is_long_lived_sse = request.method == "GET" and "text/event-stream" in request.headers.get("accept", "")
    timeout = httpx.Timeout(default_timeout, connect=10.0, read=None if is_long_lived_sse else default_timeout)
    client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
    try:
        upstream_request = client.build_request(request.method, upstream_url, params=request.query_params, content=body if body else None, headers=headers)
        upstream_response = await client.send(upstream_request, stream=True)
    except httpx.TimeoutException as exc:
        await client.aclose()
        raise HTTPException(status_code=504, detail="Upstream MCP server timed out") from exc
    except httpx.HTTPError as exc:
        await client.aclose()
        raise HTTPException(status_code=502, detail=f"Upstream MCP server connection failed: {type(exc).__name__}") from exc

    content_type = upstream_response.headers.get("content-type", "")
    response_headers = {k: v for k, v in upstream_response.headers.items() if k.lower() not in _HOP_BY_HOP and k.lower() not in {"content-encoding"}}
    response_headers["X-Content-Type-Options"] = "nosniff"
    response_headers["Cache-Control"] = "no-store"
    if "text/event-stream" in content_type:
        # Preserve long-lived server-sent events instead of buffering them in memory.
        return StreamingResponse(
            _stream_sse(upstream_response.aiter_bytes(), config, request_methods),
            status_code=upstream_response.status_code,
            headers=response_headers,
            background=BackgroundTask(_close_upstream, upstream_response, client),
            media_type=None,
        )

    try:
        response_body = await upstream_response.aread()
    finally:
        await upstream_response.aclose()
        await client.aclose()
    if request.method == "POST" and response_body and "application/json" in content_type:
        try:
            payload = json.loads(response_body)
            payload = transform_response(payload, request_methods, config)
            response_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        except (json.JSONDecodeError, TypeError):
            pass
    return Response(content=response_body, status_code=upstream_response.status_code, headers=response_headers, media_type=None)


@router.get("/gateway/{connection_id}", operation_id="gateway_root_get")
async def gateway_root_get(request: Request, connection_id: str) -> Response:
    """Proxy a Streamable HTTP MCP endpoint configured by server-side environment."""
    return await _proxy(request, connection_id)


@router.post("/gateway/{connection_id}", operation_id="gateway_root_post")
async def gateway_root_post(request: Request, connection_id: str) -> Response:
    """Forward an MCP Streamable HTTP request to an approved upstream."""
    return await _proxy(request, connection_id)


@router.delete("/gateway/{connection_id}", operation_id="gateway_root_delete")
async def gateway_root_delete(request: Request, connection_id: str) -> Response:
    """Forward an MCP session termination request to an approved upstream."""
    return await _proxy(request, connection_id)


@router.api_route("/gateway/{connection_id}/{rest:path}", methods=["GET", "POST", "DELETE"], include_in_schema=False)
async def gateway_path(request: Request, connection_id: str, rest: str) -> Response:
    return await _proxy(request, connection_id)
