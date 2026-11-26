"""Defensive request-boundary checks for a CVE-2026-5029 mitigation prototype."""
import hmac
import os
from dotenv import load_dotenv
load_dotenv()
from urllib.parse import urlsplit

CVE_ID = "CVE-2026-5029"

def _csv_env(name: str) -> set[str]:
    return {item.strip().lower() for item in os.getenv(name, "").split(",") if item.strip()}

def check_gateway_request(token: str | None, host: str | None, origin: str | None) -> dict:
    """Fail closed when the CVE lab is enabled but its secret/allowlists are absent."""
    expected = os.getenv("CANARYTRAP_CVE_TOKEN", "")
    hosts = _csv_env("CANARYTRAP_ALLOWED_HOSTS")
    origins = _csv_env("CANARYTRAP_ALLOWED_ORIGINS")
    if not expected or not hosts:
        return {"allowed": False, "status_code": 503, "reason": "CVE gateway is not configured"}
    if not token:
        return {"allowed": False, "status_code": 401, "reason": "Bearer token required"}
    if not hmac.compare_digest(token, expected):
        return {"allowed": False, "status_code": 403, "reason": "Invalid bearer token"}
    normalized_host = (host or "").split(":")[0].lower()
    if normalized_host not in hosts:
        return {"allowed": False, "status_code": 400, "reason": "Host is not allowlisted"}
    if origin:
        parsed = urlsplit(origin)
        normalized_origin = f"{parsed.scheme}://{parsed.netloc}".lower()
        if not parsed.scheme or not parsed.netloc or normalized_origin not in origins:
            return {"allowed": False, "status_code": 403, "reason": "Origin is not allowlisted"}
    return {"allowed": True, "status_code": 200, "reason": "Request passed gateway checks"}

def cve_metadata():
    return {
        "id": CVE_ID,
        "title": "Unauthenticated Code Runner MCP endpoint can permit arbitrary code execution",
        "severity": "HIGH",
        "cvss": "8.7 (CVSS 4.0, as reported in public records)",
        "weakness": "CWE-306: Missing Authentication for Critical Function",
        "scope_note": "This project demonstrates gateway-side controls. It is not an upstream vendor patch.",
        "references": [
            {"label": "NVD", "url": "https://nvd.nist.gov/vuln/detail/CVE-2026-5029"},
            {"label": "CERT Polska advisory", "url": "https://cert.pl/en/posts/2026/05/CVE-2026-5029/"},
            {"label": "GitHub Security Advisory", "url": "https://github.com/advisories/GHSA-jv4w-6p47-rhcx"},
            {"label": "Affected upstream project", "url": "https://github.com/formulahendry/mcp-server-code-runner"},
        ],
    }
