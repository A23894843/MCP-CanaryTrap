# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""HTTP Streamable MCP reverse-proxy routes for CanaryTrap.

Configure approved upstreams using CANARYTRAP_HTTP_UPSTREAMS. Secrets are referenced
by environment-variable name (token_env), never submitted through the dashboard.
"""
# Explanation: Imports names from __future__.
from __future__ import annotations

# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports names from typing.
from typing import Any

# Explanation: Imports modules that this file uses.
import httpx
# Explanation: Imports names from fastapi.
from fastapi import APIRouter, HTTPException, Request, Response
# Explanation: Imports names from fastapi.responses.
from fastapi.responses import JSONResponse, StreamingResponse
# Explanation: Imports names from starlette.background.
from starlette.background import BackgroundTask

# Explanation: Imports names from gateway_core.
from .gateway_core import GatewayRecorder, decoy_kind, inject_decoys, load_http_upstreams, request_operation, synthetic_response, transform_response
# Explanation: Imports names from security_center.
from .security_center import policy_decision, resolve_gateway_tenant

# Explanation: Assigns or updates a value used later by this function or module.
router = APIRouter(tags=["live MCP gateway"])
# Explanation: Sets a module-level constant or configuration value.
_HOP_BY_HOP = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailers", "transfer-encoding", "upgrade", "content-length", "host"}


# Explanation: Function _headers_for_upstream: implements the operation described by its name and body.
def _headers_for_upstream(request: Request, config: dict[str, Any]) -> dict[str, str]:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP and k.lower() != "authorization" and k.lower() != "x-canarytrap-api-key"}
    # Explanation: Assigns or updates a value used later by this function or module.
    token_env = str(config.get("token_env") or "").strip()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if token_env:
        # Explanation: Assigns or updates a value used later by this function or module.
        token = os.getenv(token_env, "")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not token:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=503, detail=f"Configured credential environment variable '{token_env}' is not set")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if os.getenv("APP_ENV", "development").strip().lower() == "production" and not str(config["url"]).startswith("https://"):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=422, detail="Use an HTTPS upstream URL when forwarding a bearer token in production")
        # Explanation: Assigns or updates a value used later by this function or module.
        headers["authorization"] = f"Bearer {token}"
    # Do not forward the dashboard/client Authorization header upstream: it may be
    # the CanaryTrap gateway credential rather than the upstream server credential.
    # Explanation: Return this result to the caller; this ends the current function path.
    return headers


# Explanation: Function _mutate_rpc: implements the operation described by its name and body.
def _mutate_rpc(payload: Any, config: dict[str, Any], recorder: GatewayRecorder | None = None) -> Any:
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if isinstance(payload, list):
        # Explanation: Return this result to the caller; this ends the current function path.
        return [_mutate_rpc(item, config, recorder) for item in payload]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(payload, dict):
        # Explanation: Return this result to the caller; this ends the current function path.
        return payload
    # The marker is attached by the request ID map in the caller when response method is known.
    # Explanation: Return this result to the caller; this ends the current function path.
    return inject_decoys(payload, config)


# Explanation: Async function _close_upstream: performs asynchronous work; inspect awaited calls and returned result.
async def _close_upstream(upstream_response: httpx.Response, client: httpx.AsyncClient) -> None:
    # Explanation: Waits for an asynchronous operation to complete and obtains its result.
    await upstream_response.aclose()
    # Explanation: Waits for an asynchronous operation to complete and obtains its result.
    await client.aclose()


# Explanation: Function _transform_sse_frame: implements the operation described by its name and body.
def _transform_sse_frame(frame: bytes, config: dict[str, Any], request_methods: dict[str, str]) -> bytes:
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        text = frame.decode("utf-8")
    except UnicodeDecodeError:
        # Explanation: Return this result to the caller; this ends the current function path.
        return frame + b"\n\n"
    # Explanation: Assigns or updates a value used later by this function or module.
    lines = text.splitlines()
    # Explanation: Assigns or updates a value used later by this function or module.
    data_lines = [line[5:].lstrip() for line in lines if line.startswith("data:")]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not data_lines:
        # Explanation: Return this result to the caller; this ends the current function path.
        return frame + b"\n\n"
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        payload = json.loads("\n".join(data_lines))
        # Explanation: Assigns or updates a value used later by this function or module.
        payload = transform_response(payload, request_methods, config)
        # Explanation: Assigns or updates a value used later by this function or module.
        encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        # Explanation: Assigns or updates a value used later by this function or module.
        lines = [line for line in lines if not line.startswith("data:")] + ["data: " + encoded]
        # Explanation: Return this result to the caller; this ends the current function path.
        return ("\n".join(lines) + "\n\n").encode("utf-8")
    except (json.JSONDecodeError, TypeError):
        # Explanation: Return this result to the caller; this ends the current function path.
        return frame + b"\n\n"


# Explanation: Async function _stream_sse: performs asynchronous work; inspect awaited calls and returned result.
async def _stream_sse(content, config: dict[str, Any], request_methods: dict[str, str]):
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Stream SSE frames while transforming complete JSON-RPC data messages."""
    # Explanation: Assigns or updates a value used later by this function or module.
    buffer = b""
    # Explanation: Asynchronous loop over an async iterable.
    async for chunk in content:
        # Explanation: Assigns or updates a value used later by this function or module.
        buffer += chunk
        # Explanation: Repeats the block while this condition remains true.
        while True:
            # Accept both common SSE line endings.
            # Explanation: Assigns or updates a value used later by this function or module.
            lf = buffer.find(b"\n\n")
            # Explanation: Assigns or updates a value used later by this function or module.
            crlf = buffer.find(b"\r\n\r\n")
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            candidates = [(idx, sep) for idx, sep in ((lf, b"\n\n"), (crlf, b"\r\n\r\n")) if idx >= 0]
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if not candidates:
                # Explanation: Stops the nearest enclosing loop immediately.
                break
            # Explanation: Assigns or updates a value used later by this function or module.
            idx, sep = min(candidates, key=lambda item: item[0])
            # Explanation: Assigns or updates a value used later by this function or module.
            frame, buffer = buffer[:idx], buffer[idx + len(sep):]
            # Explanation: Yields a value from a generator/stream instead of returning the whole sequence at once.
            yield _transform_sse_frame(frame, config, request_methods)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if len(buffer) > 1024 * 1024:
            # Bound memory if an upstream violates SSE framing.
            # Explanation: Yields a value from a generator/stream instead of returning the whole sequence at once.
            yield buffer
            # Explanation: Assigns or updates a value used later by this function or module.
            buffer = b""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if buffer:
        # Explanation: Yields a value from a generator/stream instead of returning the whole sequence at once.
        yield _transform_sse_frame(buffer, config, request_methods)


# Explanation: Async function _proxy: performs asynchronous work; inspect awaited calls and returned result.
async def _proxy(request: Request, connection_id: str) -> Response:
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        upstreams = load_http_upstreams()
    except ValueError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    # Explanation: Assigns or updates a value used later by this function or module.
    config = upstreams.get(connection_id)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not config:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=404, detail=f"No approved HTTP MCP upstream named '{connection_id}' is configured")
    # Explanation: Assigns or updates a value used later by this function or module.
    tenant = resolve_gateway_tenant(request.headers.get("x-canarytrap-api-key"))

    # Explanation: Assigns or updates a value used later by this function or module.
    max_body_bytes = int(os.getenv("CANARYTRAP_MAX_REQUEST_BYTES", str(2 * 1024 * 1024)))
    # Explanation: Assigns or updates a value used later by this function or module.
    content_length = request.headers.get("content-length", "")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if content_length.isdigit() and int(content_length) > max_body_bytes:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=413, detail=f"MCP request exceeds configured limit ({max_body_bytes} bytes)")
    # Explanation: Assigns or updates a value used later by this function or module.
    body = await request.body()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if len(body) > max_body_bytes:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=413, detail=f"MCP request exceeds configured limit ({max_body_bytes} bytes)")
    # Explanation: Assigns or updates a value used later by this function or module.
    message: Any = None
    # Explanation: Assigns or updates a value used later by this function or module.
    request_methods: dict[str, str] = {}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if request.method == "POST" and body:
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Assigns or updates a value used later by this function or module.
            message = json.loads(body)
        except json.JSONDecodeError:
            # Explanation: Assigns or updates a value used later by this function or module.
            message = None
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if isinstance(message, list):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise HTTPException(status_code=400, detail="JSON-RPC batch requests are not supported by the current CanaryTrap monitoring adapter")

    # Explanation: Assigns or updates a value used later by this function or module.
    recorder: GatewayRecorder | None = None
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if request.method == "POST" and isinstance(message, dict):
        # Explanation: Assigns or updates a value used later by this function or module.
        operation = request_operation(message)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if operation:
            # Explanation: Assigns or updates a value used later by this function or module.
            op, target, kind = operation
            # Explanation: Assigns or updates a value used later by this function or module.
            actual_kind = decoy_kind(target, config, kind)
            # Explanation: Assigns or updates a value used later by this function or module.
            recorder = GatewayRecorder(connection_id, request.headers.get("mcp-session-id") and ("gw-" + connection_id + "-" + request.headers["mcp-session-id"]), tenant=tenant)
            # Explanation: Assigns or updates a value used later by this function or module.
            decision = policy_decision(op, target, kind, tenant)
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            recorder.record(op, target[:250], kind, actual_kind == kind, f"HTTP MCP request observed; policy={decision['action']}; arguments omitted", policy_action=decision["action"])
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if decision["action"] == "deny":
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if message.get("id") is None:
                    # Explanation: Return this result to the caller; this ends the current function path.
                    return Response(status_code=202, headers={"MCP-CanaryTrap-Policy": "denied"})
                # Explanation: Assigns or updates a value used later by this function or module.
                denied = {"jsonrpc":"2.0","id":message.get("id"),"error":{"code":-32001,"message":"Blocked by MCP-CanaryTrap policy","data":{"rule_id":decision.get("rule_id"),"rule_name":decision.get("rule_name")}}}
                # Explanation: Return this result to the caller; this ends the current function path.
                return JSONResponse(denied, headers={"MCP-CanaryTrap-Policy": "denied"})
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if actual_kind == kind:
                # Explanation: Assigns or updates a value used later by this function or module.
                result = synthetic_response(message, kind, target)
                # Explanation: Conditional decision: execute the following branch only when this expression is true.
                if result is None:
                    # Explanation: Return this result to the caller; this ends the current function path.
                    return Response(status_code=202)
                # Explanation: Return this result to the caller; this ends the current function path.
                return JSONResponse(result, headers={"MCP-CanaryTrap-Event": "decoy-interaction-recorded"})
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if message.get("method") and message.get("id") is not None:
            # Explanation: Assigns or updates a value used later by this function or module.
            request_methods[str(message["id"])] = str(message["method"])

    # Explanation: Assigns or updates a value used later by this function or module.
    upstream_url = config["url"]
    # Optional path suffix lets clients use /gateway/<id>/<endpoint-suffix> when required.
    # Explanation: Assigns or updates a value used later by this function or module.
    route_suffix = request.path_params.get("rest", "")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if route_suffix:
        # Explanation: Assigns or updates a value used later by this function or module.
        upstream_url = upstream_url.rstrip("/") + "/" + route_suffix.lstrip("/")
    # Explanation: Assigns or updates a value used later by this function or module.
    headers = _headers_for_upstream(request, config)
    # Explanation: Assigns or updates a value used later by this function or module.
    default_timeout = float(os.getenv("CANARYTRAP_UPSTREAM_TIMEOUT", "60"))
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    is_long_lived_sse = request.method == "GET" and "text/event-stream" in request.headers.get("accept", "")
    # Explanation: Assigns or updates a value used later by this function or module.
    timeout = httpx.Timeout(default_timeout, connect=10.0, read=None if is_long_lived_sse else default_timeout)
    # Explanation: Assigns or updates a value used later by this function or module.
    client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        upstream_request = client.build_request(request.method, upstream_url, params=request.query_params, content=body if body else None, headers=headers)
        # Explanation: Assigns or updates a value used later by this function or module.
        upstream_response = await client.send(upstream_request, stream=True)
    except httpx.TimeoutException as exc:
        # Explanation: Waits for an asynchronous operation to complete and obtains its result.
        await client.aclose()
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=504, detail="Upstream MCP server timed out") from exc
    except httpx.HTTPError as exc:
        # Explanation: Waits for an asynchronous operation to complete and obtains its result.
        await client.aclose()
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise HTTPException(status_code=502, detail=f"Upstream MCP server connection failed: {type(exc).__name__}") from exc

    # Explanation: Assigns or updates a value used later by this function or module.
    content_type = upstream_response.headers.get("content-type", "")
    # Explanation: Assigns or updates a value used later by this function or module.
    response_headers = {k: v for k, v in upstream_response.headers.items() if k.lower() not in _HOP_BY_HOP and k.lower() not in {"content-encoding"}}
    # Explanation: Assigns or updates a value used later by this function or module.
    response_headers["X-Content-Type-Options"] = "nosniff"
    # Explanation: Assigns or updates a value used later by this function or module.
    response_headers["Cache-Control"] = "no-store"
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if "text/event-stream" in content_type:
        # Preserve long-lived server-sent events instead of buffering them in memory.
        # Explanation: Return this result to the caller; this ends the current function path.
        return StreamingResponse(
            _stream_sse(upstream_response.aiter_bytes(), config, request_methods),
            status_code=upstream_response.status_code,
            headers=response_headers,
            background=BackgroundTask(_close_upstream, upstream_response, client),
            media_type=None,
        )

    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        response_body = await upstream_response.aread()
    finally:
        # Explanation: Waits for an asynchronous operation to complete and obtains its result.
        await upstream_response.aclose()
        # Explanation: Waits for an asynchronous operation to complete and obtains its result.
        await client.aclose()
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if request.method == "POST" and response_body and "application/json" in content_type:
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Assigns or updates a value used later by this function or module.
            payload = json.loads(response_body)
            # Explanation: Assigns or updates a value used later by this function or module.
            payload = transform_response(payload, request_methods, config)
            # Explanation: Assigns or updates a value used later by this function or module.
            response_body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        except (json.JSONDecodeError, TypeError):
            # Explanation: Intentional no-op placeholder; this block performs no action.
            pass
    # Explanation: Return this result to the caller; this ends the current function path.
    return Response(content=response_body, status_code=upstream_response.status_code, headers=response_headers, media_type=None)


@router.get("/gateway/{connection_id}", operation_id="gateway_root_get")
# Explanation: Async function gateway_root_get: performs asynchronous work; inspect awaited calls and returned result.
async def gateway_root_get(request: Request, connection_id: str) -> Response:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Proxy a Streamable HTTP MCP endpoint configured by server-side environment."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return await _proxy(request, connection_id)


@router.post("/gateway/{connection_id}", operation_id="gateway_root_post")
# Explanation: Async function gateway_root_post: performs asynchronous work; inspect awaited calls and returned result.
async def gateway_root_post(request: Request, connection_id: str) -> Response:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Forward an MCP Streamable HTTP request to an approved upstream."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return await _proxy(request, connection_id)


@router.delete("/gateway/{connection_id}", operation_id="gateway_root_delete")
# Explanation: Async function gateway_root_delete: performs asynchronous work; inspect awaited calls and returned result.
async def gateway_root_delete(request: Request, connection_id: str) -> Response:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Forward an MCP session termination request to an approved upstream."""
    # Explanation: Return this result to the caller; this ends the current function path.
    return await _proxy(request, connection_id)


@router.api_route("/gateway/{connection_id}/{rest:path}", methods=["GET", "POST", "DELETE"], include_in_schema=False)
# Explanation: Async function gateway_path: performs asynchronous work; inspect awaited calls and returned result.
async def gateway_path(request: Request, connection_id: str, rest: str) -> Response:
    # Explanation: Return this result to the caller; this ends the current function path.
    return await _proxy(request, connection_id)
