"""Opt-in request guard for the CVE-2026-5029 mitigation profile.

This is a gateway-side compensating control. It does not patch the upstream
Code Runner MCP Server; keep that service private and reachable only by this gateway.
"""
from __future__ import annotations

import os
from urllib.parse import urlsplit

from fastapi import HTTPException, Request

from .security_center import resolve_gateway_tenant


def _csv_env(name: str) -> set[str]:
    return {item.strip().lower() for item in os.getenv(name, "").split(",") if item.strip()}


def _host(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = urlsplit("//" + value)
        return (parsed.hostname or "").rstrip(".").lower()
    except ValueError:
        return ""


def _origin(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return ""
        host = parsed.hostname.rstrip(".").lower()
        port = parsed.port
        default = (parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80)
        authority = host if port is None or default else f"{host}:{port}"
        return f"{parsed.scheme.lower()}://{authority}"
    except ValueError:
        return ""


def enforce_cve_2026_5029_request(request: Request) -> str | None:
    """Enforce strict host/origin/API-key checks when the profile is enabled.

    Returns the resolved tenant. Raises HTTPException on invalid configuration
    or request. Disabled by default to preserve local-development compatibility.
    """
    enabled = os.getenv("CANARYTRAP_CVE_2026_5029_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}
    if not enabled:
        return None

    allowed_hosts = _csv_env("CANARYTRAP_CVE_ALLOWED_HOSTS")
    allowed_origins = {
        origin for item in os.getenv("CANARYTRAP_CVE_ALLOWED_ORIGINS", "").split(",")
        if (origin := _origin(item.strip()))
    }
    if not allowed_hosts or not allowed_origins:
        raise HTTPException(status_code=503, detail="CVE-2026-5029 profile requires CANARYTRAP_CVE_ALLOWED_HOSTS and CANARYTRAP_CVE_ALLOWED_ORIGINS")

    incoming_host = _host(request.headers.get("host"))
    if not incoming_host or incoming_host not in allowed_hosts:
        raise HTTPException(status_code=400, detail="Request Host is not allowed")

    origin_header = request.headers.get("origin")
    if origin_header:
        incoming_origin = _origin(origin_header)
        if not incoming_origin or incoming_origin not in allowed_origins:
            raise HTTPException(status_code=403, detail="Request Origin is not allowed")

    api_key = request.headers.get("x-canarytrap-api-key")
    if not api_key:
        raise HTTPException(status_code=401, detail="Gateway API key required by CVE-2026-5029 protection profile")
    if not os.getenv("CANARYTRAP_RBAC_KEYS", "").strip():
        raise HTTPException(status_code=503, detail="CVE-2026-5029 profile requires a configured CANARYTRAP_RBAC_KEYS map")

    return resolve_gateway_tenant(api_key)
