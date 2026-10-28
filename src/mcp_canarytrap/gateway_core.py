"""Shared JSON-RPC helpers for transport-aware MCP monitoring adapters.

This module deliberately logs operation names and targets, not arbitrary tool
arguments or tool results, to reduce accidental capture of sensitive data.
"""
from __future__ import annotations

import json
import logging
import ipaddress
import os
import re
import uuid
from urllib.parse import urlsplit
from typing import Any
from pathlib import Path

from .events import InteractionEvent
from .storage import Store
from .verdict import evaluate_session

_STORE_CACHE: dict[str, Store] = {}
logger = logging.getLogger(__name__)


def get_store() -> Store:
    """Reuse one SQLite Store per configured database path within this process."""
    path = str(Path(os.getenv("CANARYTRAP_DB", "canarytrap.sqlite3")).resolve())
    if path not in _STORE_CACHE:
        _STORE_CACHE[path] = Store(path)
    return _STORE_CACHE[path]


def validate_upstream_url(url: str) -> None:
    """Reject obvious local/metadata destinations unless an operator opts in."""
    parsed = urlsplit(url)
    if parsed.query or parsed.fragment:
        raise ValueError("Upstream URLs must not contain query strings or fragments; configure credentials separately")
    host = (parsed.hostname or "").lower().rstrip(".")
    allow_private = os.getenv("CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS", "false").strip().lower() in {"1","true","yes"}
    blocked_names = {"metadata", "metadata.google.internal", "metadata.azure.internal", "instance-data"}
    if host in blocked_names:
        raise ValueError("Cloud metadata hostnames are blocked as upstream destinations")
    if host.endswith((".localhost", ".local", ".internal")) and not allow_private:
        raise ValueError("Local/internal upstream hostnames require CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS=true")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address and not address.is_global and not allow_private:
        raise ValueError("Private, loopback, link-local, and reserved IP upstreams are blocked by default")
    allowed = [x.strip().lower() for x in os.getenv("CANARYTRAP_ALLOWED_UPSTREAM_HOSTS", "").split(",") if x.strip()]
    if allowed and host not in allowed:
        raise ValueError("Upstream hostname is not in CANARYTRAP_ALLOWED_UPSTREAM_HOSTS")

def load_http_upstreams() -> dict[str, dict[str, Any]]:
    """Load allow-listed HTTP upstreams from CANARYTRAP_HTTP_UPSTREAMS JSON.

    Example: {"docs":{"url":"https://mcp.example.com/mcp",
      "token_env":"DOCS_MCP_TOKEN","decoy_tools":["canarytrap_decoy_admin"],
      "decoy_resources":["canarytrap://secret/payroll"],
      "decoy_prompts":["canarytrap_decoy_system_prompt"]}}
    """
    raw = os.getenv("CANARYTRAP_HTTP_UPSTREAMS", "{}").strip() or "{}"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("CANARYTRAP_HTTP_UPSTREAMS must be valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("CANARYTRAP_HTTP_UPSTREAMS must be a JSON object")
    clean: dict[str, dict[str, Any]] = {}
    for key, value in parsed.items():
        if not isinstance(key, str) or not key.replace("-", "").replace("_", "").isalnum():
            raise ValueError("HTTP upstream IDs may contain only letters, numbers, hyphens, and underscores")
        if not isinstance(value, dict) or not isinstance(value.get("url"), str):
            raise ValueError(f"HTTP upstream '{key}' must have a url")
        url = value["url"].strip()
        parsed_url = urlsplit(url)
        if parsed_url.scheme not in {"https", "http"} or not parsed_url.hostname:
            raise ValueError(f"HTTP upstream '{key}' URL must be a valid http:// or https:// URL")
        if parsed_url.username or parsed_url.password:
            raise ValueError(f"HTTP upstream '{key}' URL must not embed username/password credentials")
        try:
            validate_upstream_url(url)
        except ValueError as exc:
            raise ValueError(f"HTTP upstream '{key}': {exc}") from exc
        for field in ("decoy_tools", "decoy_resources", "decoy_prompts"):
            if field in value and (not isinstance(value[field], list) or not all(isinstance(x, str) and x.strip() for x in value[field])):
                raise ValueError(f"HTTP upstream '{key}' field '{field}' must be a list of non-empty strings")
        token_env = value.get("token_env", "")
        if not isinstance(token_env, str) or (token_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token_env)):
            raise ValueError(f"HTTP upstream '{key}' token_env must be a valid environment-variable name")
        clean[key] = {
            "url": url,
            "token_env": token_env,
            "decoy_tools": list(dict.fromkeys(value.get("decoy_tools", []))),
            "decoy_resources": list(dict.fromkeys(value.get("decoy_resources", []))),
            "decoy_prompts": list(dict.fromkeys(value.get("decoy_prompts", []))),
        }
    # Dashboard-saved definitions contain no secret values. They can be edited without
    # redeploying; the hosting environment remains the source for referenced credentials.
    clean.update(get_store().list_gateway_connections())
    return clean


class GatewayRecorder:
    """Persist gateway interactions with the same deterministic verdict engine."""
    def __init__(self, connection_id: str, session_id: str | None = None, tenant: str | None = None):
        self.connection_id = connection_id
        self.tenant = tenant or os.getenv("CANARYTRAP_DEFAULT_TENANT", "default")
        self.session_id = session_id or f"gw-{connection_id}-{uuid.uuid4().hex[:12]}"
        self.store = get_store()
        existing = self.store.get_session(self.session_id, tenant=self.tenant)
        if not existing:
            from datetime import datetime, timezone
            self.store.create_session(self.session_id, f"live-gateway:{connection_id}", datetime.now(timezone.utc).isoformat(), tenant=self.tenant)

    def record(self, operation: str, target: str, kind: str, is_decoy: bool, details: str = "", policy_action: str = "allow") -> dict[str, Any]:
        event = InteractionEvent.create(self.session_id, operation, target, kind, is_decoy, details)
        self.store.add_event(event)
        events = [InteractionEvent(**{**e, "is_decoy": bool(e["is_decoy"])}) for e in self.store.list_events(self.session_id)]
        verdict = evaluate_session(self.session_id, events)
        self.store.save_verdict(verdict)
        # Security Center maintains a tenant-scoped hash-chained audit trail and
        # deterministic frequency baseline for observed gateway operations.
        try:
            from .security_center import record_gateway_event
            record_gateway_event(operation, target, is_decoy, verdict.status, self.connection_id, self.tenant, policy_action)
        except Exception:
            # Audit extension failures must not crash an MCP request path, but are
            # visible to server operators rather than silently discarded.
            logger.exception("CanaryTrap Security Center audit/baseline extension failed")
        return {"event": event.to_dict(), "verdict": verdict.to_dict()}


def request_operation(message: Any) -> tuple[str, str, str] | None:
    """Return operation, target and target kind for supported MCP request messages."""
    if not isinstance(message, dict) or not isinstance(message.get("method"), str):
        return None
    method = message["method"]
    params = message.get("params") or {}
    if not isinstance(params, dict):
        params = {}
    if method == "tools/call":
        target = params.get("name", "")
        return (method, str(target), "tool") if target else (method, "<missing-name>", "tool")
    if method == "resources/read":
        target = params.get("uri", "")
        return (method, str(target), "resource") if target else (method, "<missing-uri>", "resource")
    if method == "prompts/get":
        target = params.get("name", "")
        return (method, str(target), "prompt") if target else (method, "<missing-name>", "prompt")
    return None


def decoy_kind(target: str, config: dict[str, Any], expected_kind: str | None = None) -> str | None:
    """Return the configured decoy kind, optionally scoped to the operation kind."""
    fields = {"tool": "decoy_tools", "resource": "decoy_resources", "prompt": "decoy_prompts"}
    kinds = [expected_kind] if expected_kind in fields else list(fields)
    for kind in kinds:
        if target in config.get(fields[kind], []):
            return kind
    return None


def inject_decoys(message: Any, config: dict[str, Any]) -> Any:
    """Inject synthetic decoy definitions into successful list responses."""
    if not isinstance(message, dict) or not isinstance(message.get("result"), dict):
        return message
    method = message.get("_canarytrap_method")
    result = message["result"]
    if method == "tools/list" and isinstance(result.get("tools"), list):
        present = {x.get("name") for x in result["tools"] if isinstance(x, dict)}
        result["tools"].extend({
            "name": name,
            "description": "Synthetic MCP-CanaryTrap decoy. Access is monitored and will be flagged.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        } for name in config.get("decoy_tools", []) if name not in present)
    elif method == "resources/list" and isinstance(result.get("resources"), list):
        present = {x.get("uri") for x in result["resources"] if isinstance(x, dict)}
        result["resources"].extend({
            "uri": uri, "name": "CanaryTrap synthetic decoy resource", "description": "Synthetic decoy; access is monitored.", "mimeType": "text/plain"
        } for uri in config.get("decoy_resources", []) if uri not in present)
    elif method == "prompts/list" and isinstance(result.get("prompts"), list):
        present = {x.get("name") for x in result["prompts"] if isinstance(x, dict)}
        result["prompts"].extend({
            "name": name, "description": "Synthetic CanaryTrap decoy prompt; access is monitored.", "arguments": []
        } for name in config.get("decoy_prompts", []) if name not in present)
    message.pop("_canarytrap_method", None)
    return message


def synthetic_response(request_message: dict[str, Any], kind: str, target: str) -> dict[str, Any] | None:
    """Create a standards-shaped JSON-RPC result for a decoy interaction."""
    if "id" not in request_message:  # JSON-RPC notification: record, but don't reply.
        return None
    base = {"jsonrpc": "2.0", "id": request_message["id"]}
    text = f"Synthetic CanaryTrap {kind} '{target}' accessed. The interaction has been recorded."
    if kind == "tool":
        base["result"] = {"content": [{"type": "text", "text": text}], "isError": False}
    elif kind == "resource":
        base["result"] = {"contents": [{"uri": target, "mimeType": "text/plain", "text": text}]}
    else:
        base["result"] = {"description": "Synthetic monitored decoy prompt", "messages": [{"role": "user", "content": {"type": "text", "text": text}}]}
    return base


def transform_response(payload: Any, request_methods: dict[str, str], config: dict[str, Any]) -> Any:
    """Inject decoys into JSON-RPC responses using the original request ID map."""
    if isinstance(payload, list):
        return [transform_response(item, request_methods, config) for item in payload]
    if not isinstance(payload, dict) or "id" not in payload:
        return payload
    method = request_methods.get(str(payload["id"]))
    if method:
        payload["_canarytrap_method"] = method
    return inject_decoys(payload, config)
