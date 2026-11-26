"""Strict validation for OAuth authorization_endpoint URLs.

This is a defensive policy validator, not a complete OAuth implementation.
It deliberately accepts HTTPS URLs only and rejects shell-control characters.
"""
from urllib.parse import unquote, urlsplit
import re

SHELL_META = re.compile(r"""[;&|`$<>\\\r\n]""")

def validate_authorization_endpoint(value: str) -> dict:
    if not isinstance(value, str) or not value.strip():
        return {"allowed": False, "reason": "Endpoint must be a non-empty string."}
    value = value.strip()
    if len(value) > 2048:
        return {"allowed": False, "reason": "Endpoint exceeds the 2048-character policy limit."}
    decoded = unquote(value)
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in decoded):
        return {"allowed": False, "reason": "Control characters are not allowed."}
    if SHELL_META.search(decoded):
        return {"allowed": False, "reason": "Shell-control characters are not allowed in this endpoint."}
    try:
        parsed = urlsplit(value)
        # Accessing .port also validates malformed port syntax.
        port = parsed.port
    except ValueError:
        return {"allowed": False, "reason": "Malformed URL or port."}
    if parsed.scheme.lower() != "https":
        return {"allowed": False, "reason": "Only HTTPS authorization endpoints are permitted."}
    if not parsed.hostname:
        return {"allowed": False, "reason": "A hostname is required."}
    if parsed.username or parsed.password:
        return {"allowed": False, "reason": "Embedded URL credentials are not permitted."}
    if port is not None and not (1 <= port <= 65535):
        return {"allowed": False, "reason": "Port is outside the valid range."}
    return {"allowed": True, "reason": "Endpoint passed the local URL policy.", "normalized_url": value}
