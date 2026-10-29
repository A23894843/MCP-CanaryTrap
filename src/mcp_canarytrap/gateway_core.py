# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Shared JSON-RPC helpers for transport-aware MCP monitoring adapters.

This module deliberately logs operation names and targets, not arbitrary tool
arguments or tool results, to reduce accidental capture of sensitive data.
"""
# Explanation: Imports names from __future__.
from __future__ import annotations

# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import logging
# Explanation: Imports modules that this file uses.
import ipaddress
# Explanation: Imports modules that this file uses.
import os
# Explanation: Imports modules that this file uses.
import re
# Explanation: Imports modules that this file uses.
import uuid
# Explanation: Imports names from urllib.parse.
from urllib.parse import urlsplit
# Explanation: Imports names from typing.
from typing import Any
# Explanation: Imports names from pathlib.
from pathlib import Path

# Explanation: Imports names from events.
from .events import InteractionEvent
# Explanation: Imports names from storage.
from .storage import Store
# Explanation: Imports names from verdict.
from .verdict import evaluate_session

# Explanation: Assigns or updates a value used later by this function or module.
_STORE_CACHE: dict[str, Store] = {}
# Explanation: Assigns or updates a value used later by this function or module.
logger = logging.getLogger(__name__)


# Explanation: Function get_store: Reuse one SQLite Store per configured database path within this process.
def get_store() -> Store:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Reuse one SQLite Store per configured database path within this process."""
    # Explanation: Assigns or updates a value used later by this function or module.
    path = str(Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")).resolve())
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if path not in _STORE_CACHE:
        # Explanation: Assigns or updates a value used later by this function or module.
        _STORE_CACHE[path] = Store(path)
    # Explanation: Return this result to the caller; this ends the current function path.
    return _STORE_CACHE[path]


# Explanation: Function validate_upstream_url: Reject obvious local/metadata destinations unless an operator opts in.
def validate_upstream_url(url: str) -> None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Reject obvious local/metadata destinations unless an operator opts in."""
    # Explanation: Assigns or updates a value used later by this function or module.
    parsed = urlsplit(url)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if parsed.query or parsed.fragment:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("Upstream URLs must not contain query strings or fragments; configure credentials separately")
    # Explanation: Assigns or updates a value used later by this function or module.
    host = (parsed.hostname or "").lower().rstrip(".")
    # Explanation: Assigns or updates a value used later by this function or module.
    allow_private = os.getenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS", "false").strip().lower() in {"1","true","yes"}
    # Explanation: Assigns or updates a value used later by this function or module.
    blocked_names = {"metadata", "metadata.google.internal", "metadata.azure.internal", "instance-data"}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if host in blocked_names:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("Cloud metadata hostnames are blocked as upstream destinations")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if host.endswith((".localhost", ".local", ".internal")) and not allow_private:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("Local/internal upstream hostnames require CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS=true")
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        address = ipaddress.ip_address(host)
    except ValueError:
        # Explanation: Assigns or updates a value used later by this function or module.
        address = None
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if address and not address.is_global and not allow_private:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("Private, loopback, link-local, and reserved IP upstreams are blocked by default")
    # Explanation: Assigns or updates a value used later by this function or module.
    allowed = [x.strip().lower() for x in os.getenv("CANARYTRAP_ALLOWED_UPSTREAM_HOSTS", "").split(",") if x.strip()]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if allowed and host not in allowed:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("Upstream hostname is not in CANARYTRAP_ALLOWED_UPSTREAM_HOSTS")

# Explanation: Function load_http_upstreams: Load allow-listed HTTP upstreams from CANARYTRAP_HTTP_UPSTREAMS JSON.  Example: {"docs":{"url":"https://mcp.example.com/mcp",   "token_env":"DOCS_MCP_TOKEN","decoy_tools":["canarytrap_decoy_admin"],   "decoy_resources":["canarytrap://secret/payroll"],   "decoy_prompts":["canarytrap_decoy_system_prompt"]}}
def load_http_upstreams() -> dict[str, dict[str, Any]]:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Load allow-listed HTTP upstreams from CANARYTRAP_HTTP_UPSTREAMS JSON.

    Example: {"docs":{"url":"https://mcp.example.com/mcp",
      "token_env":"DOCS_MCP_TOKEN","decoy_tools":["canarytrap_decoy_admin"],
      "decoy_resources":["canarytrap://secret/payroll"],
      "decoy_prompts":["canarytrap_decoy_system_prompt"]}}
    """
    # Explanation: Assigns or updates a value used later by this function or module.
    raw = os.getenv("CANARYTRAP_HTTP_UPSTREAMS", "{}").strip() or "{}"
    # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
    try:
        # Explanation: Assigns or updates a value used later by this function or module.
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("CANARYTRAP_HTTP_UPSTREAMS must be valid JSON") from exc
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(parsed, dict):
        # Explanation: Raise an exception to reject the operation or report a failure.
        raise ValueError("CANARYTRAP_HTTP_UPSTREAMS must be a JSON object")
    # Explanation: Assigns or updates a value used later by this function or module.
    clean: dict[str, dict[str, Any]] = {}
    # Explanation: Loop over each item in the iterable and run the indented body.
    for key, value in parsed.items():
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not isinstance(key, str) or not key.replace("-", "").replace("_", "").isalnum():
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError("HTTP upstream IDs may contain only letters, numbers, hyphens, and underscores")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not isinstance(value, dict) or not isinstance(value.get("url"), str):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError(f"HTTP upstream '{key}' must have a url")
        # Explanation: Assigns or updates a value used later by this function or module.
        url = value["url"].strip()
        # Explanation: Assigns or updates a value used later by this function or module.
        parsed_url = urlsplit(url)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError(f"HTTP upstream '{key}' URL must be a valid http:// or https:// URL")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if parsed_url.username or parsed_url.password:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError(f"HTTP upstream '{key}' URL must not embed username/password credentials")
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            validate_upstream_url(url)
        except ValueError as exc:
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError(f"HTTP upstream '{key}': {exc}") from exc
        # Explanation: Loop over each item in the iterable and run the indented body.
        for field in ("decoy_tools", "decoy_resources", "decoy_prompts"):
            # Explanation: Conditional decision: execute the following branch only when this expression is true.
            if field in value and (not isinstance(value[field], list) or not all(isinstance(x, str) and x.strip() for x in value[field])):
                # Explanation: Raise an exception to reject the operation or report a failure.
                raise ValueError(f"HTTP upstream '{key}' field '{field}' must be a list of non-empty strings")
        # Explanation: Assigns or updates a value used later by this function or module.
        token_env = value.get("token_env", "")
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not isinstance(token_env, str) or (token_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env)):
            # Explanation: Raise an exception to reject the operation or report a failure.
            raise ValueError(f"HTTP upstream '{key}' token_env must be a valid environment-variable name")
        # Explanation: Assigns or updates a value used later by this function or module.
        clean[key] = {
            "url": url,
            "token_env": token_env,
            "decoy_tools": list(dict.fromkeys(value.get("decoy_tools", []))),
            "decoy_resources": list(dict.fromkeys(value.get("decoy_resources", []))),
            "decoy_prompts": list(dict.fromkeys(value.get("decoy_prompts", []))),
        }
    # Dashboard-saved definitions contain no secret values. They can be edited without
    # redeploying; the hosting environment remains the source for referenced credentials.
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    clean.update(get_store().list_gateway_connections())
    # Explanation: Return this result to the caller; this ends the current function path.
    return clean


# Explanation: Class GatewayRecorder: groups related data and operations.
class GatewayRecorder:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Persist gateway interactions with the same deterministic verdict engine."""
    # Explanation: Function __init__: implements the operation described by its name and body.
    def __init__(self, connection_id: str, session_id: str | None = None, tenant: str | None = None):
        # Explanation: Assigns or updates a value used later by this function or module.
        self.connection_id = connection_id
        # Explanation: Assigns or updates a value used later by this function or module.
        self.tenant = tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT", "default")
        # Explanation: Assigns or updates a value used later by this function or module.
        self.session_id = session_id or f"gw-{connection_id}-{uuid.uuid4().hex[:12]}"
        # Explanation: Assigns or updates a value used later by this function or module.
        self.store = get_store()
        # Explanation: Assigns or updates a value used later by this function or module.
        existing = self.store.get_session(self.session_id, tenant=self.tenant)
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if not existing:
            # Explanation: Imports names from datetime.
            from datetime import datetime, timezone
            # Explanation: Assigns or updates a value used later by this function or module.
            self.store.create_session(self.session_id, f"live-gateway:{connection_id}", datetime.now(timezone.utc).isoformat(), tenant=self.tenant)

    # Explanation: Function record: implements the operation described by its name and body.
    def record(self, operation: str, target: str, kind: str, is_decoy: bool, details: str = "", policy_action: str = "allow") -> dict[str, Any]:
        # Explanation: Assigns or updates a value used later by this function or module.
        event = InteractionEvent.create(self.session_id, operation, target, kind, is_decoy, details)
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        self.store.add_event(event)
        # Explanation: Assigns or updates a value used later by this function or module.
        events = [InteractionEvent(**{**e, "is_decoy": bool(e["is_decoy"])}) for e in self.store.list_events(self.session_id)]
        # Explanation: Assigns or updates a value used later by this function or module.
        verdict = evaluate_session(self.session_id, events)
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        self.store.save_verdict(verdict)
        # Security Center maintains a tenant-scoped hash-chained audit trail and
        # deterministic frequency baseline for observed gateway operations.
        # Explanation: Start exception-handling region; following except/finally clauses define failure and cleanup behaviour.
        try:
            # Explanation: Imports names from security_center.
            from .security_center import record_gateway_event
            # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
            record_gateway_event(operation, target, is_decoy, verdict.status, self.connection_id, self.tenant, policy_action)
        except Exception:
            # Audit extension failures must not crash an MCP request path, but are
            # visible to server operators rather than silently discarded.
            # Explanation: Produces a return value or diagnostic output; check the expression to see exactly what is emitted.
            logger.exception("CanaryTrap Security Center audit/baseline extension failed")
        # Explanation: Return this result to the caller; this ends the current function path.
        return {"event": event.to_dict(), "verdict": verdict.to_dict()}


# Explanation: Function request_operation: Return operation, target and target kind for supported MCP request messages.
def request_operation(message: Any) -> tuple[str, str, str] | None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Return operation, target and target kind for supported MCP request messages."""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(message, dict) or not isinstance(message.get("method"), str):
        # Explanation: Return this result to the caller; this ends the current function path.
        return None
    # Explanation: Assigns or updates a value used later by this function or module.
    method = message["method"]
    # Explanation: Assigns or updates a value used later by this function or module.
    params = message.get("params") or {}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(params, dict):
        # Explanation: Assigns or updates a value used later by this function or module.
        params = {}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if method == "tools/call":
        # Explanation: Assigns or updates a value used later by this function or module.
        target = params.get("name", "")
        # Explanation: Return this result to the caller; this ends the current function path.
        return (method, str(target), "tool") if target else (method, "<missing-name>", "tool")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if method == "resources/read":
        # Explanation: Assigns or updates a value used later by this function or module.
        target = params.get("uri", "")
        # Explanation: Return this result to the caller; this ends the current function path.
        return (method, str(target), "resource") if target else (method, "<missing-uri>", "resource")
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if method == "prompts/get":
        # Explanation: Assigns or updates a value used later by this function or module.
        target = params.get("name", "")
        # Explanation: Return this result to the caller; this ends the current function path.
        return (method, str(target), "prompt") if target else (method, "<missing-name>", "prompt")
    # Explanation: Return this result to the caller; this ends the current function path.
    return None


# Explanation: Function decoy_kind: Return the configured decoy kind, optionally scoped to the operation kind.
def decoy_kind(target: str, config: dict[str, Any], expected_kind: str | None = None) -> str | None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Return the configured decoy kind, optionally scoped to the operation kind."""
    # Explanation: Assigns or updates a value used later by this function or module.
    fields = {"tool": "decoy_tools", "resource": "decoy_resources", "prompt": "decoy_prompts"}
    # Explanation: Assigns or updates a value used later by this function or module.
    kinds = [expected_kind] if expected_kind in fields else list(fields)
    # Explanation: Loop over each item in the iterable and run the indented body.
    for kind in kinds:
        # Explanation: Conditional decision: execute the following branch only when this expression is true.
        if target in config.get(fields[kind], []):
            # Explanation: Return this result to the caller; this ends the current function path.
            return kind
    # Explanation: Return this result to the caller; this ends the current function path.
    return None


# Explanation: Function inject_decoys: Inject synthetic decoy definitions into successful list responses.
def inject_decoys(message: Any, config: dict[str, Any]) -> Any:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Inject synthetic decoy definitions into successful list responses."""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(message, dict) or not isinstance(message.get("result"), dict):
        # Explanation: Return this result to the caller; this ends the current function path.
        return message
    # Explanation: Assigns or updates a value used later by this function or module.
    method = message.get("_canarytrap_method")
    # Explanation: Assigns or updates a value used later by this function or module.
    result = message["result"]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if method == "tools/list" and isinstance(result.get("tools"), list):
        # Explanation: Assigns or updates a value used later by this function or module.
        present = {x.get("name") for x in result["tools"] if isinstance(x, dict)}
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        result["tools"].extend({
            "name": name,
            "description": "Synthetic MCP-CanaryTrap decoy. Access is monitored and will be flagged.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        } for name in config.get("decoy_tools", []) if name not in present)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    elif method == "resources/list" and isinstance(result.get("resources"), list):
        # Explanation: Assigns or updates a value used later by this function or module.
        present = {x.get("uri") for x in result["resources"] if isinstance(x, dict)}
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        result["resources"].extend({
            "uri": uri, "name": "CanaryTrap synthetic decoy resource", "description": "Synthetic decoy; access is monitored.", "mimeType": "text/plain"
        } for uri in config.get("decoy_resources", []) if uri not in present)
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    elif method == "prompts/list" and isinstance(result.get("prompts"), list):
        # Explanation: Assigns or updates a value used later by this function or module.
        present = {x.get("name") for x in result["prompts"] if isinstance(x, dict)}
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        result["prompts"].extend({
            "name": name, "description": "Synthetic CanaryTrap decoy prompt; access is monitored.", "arguments": []
        } for name in config.get("decoy_prompts", []) if name not in present)
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    message.pop("_canarytrap_method", None)
    # Explanation: Return this result to the caller; this ends the current function path.
    return message


# Explanation: Function synthetic_response: Create a standards-shaped JSON-RPC result for a decoy interaction.
def synthetic_response(request_message: dict[str, Any], kind: str, target: str) -> dict[str, Any] | None:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Create a standards-shaped JSON-RPC result for a decoy interaction."""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if "id" not in request_message:  # JSON-RPC notification: record, but don't reply.
        # Explanation: Return this result to the caller; this ends the current function path.
        return None
    # Explanation: Assigns or updates a value used later by this function or module.
    base = {"jsonrpc": "2.0", "id": request_message["id"]}
    # Explanation: Assigns or updates a value used later by this function or module.
    text = f"Synthetic CanaryTrap {kind} '{target}' accessed. The interaction has been recorded."
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if kind == "tool":
        # Explanation: Assigns or updates a value used later by this function or module.
        base["result"] = {"content": [{"type": "text", "text": text}], "isError": False}
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    elif kind == "resource":
        # Explanation: Assigns or updates a value used later by this function or module.
        base["result"] = {"contents": [{"uri": target, "mimeType": "text/plain", "text": text}]}
    else:
        # Explanation: Assigns or updates a value used later by this function or module.
        base["result"] = {"description": "Synthetic monitored decoy prompt", "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
    # Explanation: Return this result to the caller; this ends the current function path.
    return base


# Explanation: Function transform_response: Inject decoys into JSON-RPC responses using the original request ID map.
def transform_response(payload: Any, request_methods: dict[str, str], config: dict[str, Any]) -> Any:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """Inject decoys into JSON-RPC responses using the original request ID map."""
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if isinstance(payload, list):
        # Explanation: Return this result to the caller; this ends the current function path.
        return [transform_response(item, request_methods, config) for item in payload]
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if not isinstance(payload, dict) or "id" not in payload:
        # Explanation: Return this result to the caller; this ends the current function path.
        return payload
    # Explanation: Assigns or updates a value used later by this function or module.
    method = request_methods.get(str(payload["id"]))
    # Explanation: Conditional decision: execute the following branch only when this expression is true.
    if method:
        # Explanation: Assigns or updates a value used later by this function or module.
        payload["_canarytrap_method"] = method
    # Explanation: Return this result to the caller; this ends the current function path.
    return inject_decoys(payload, config)
