"""Manual smoke checks for the CVE-2026-5029 gateway guard (no pytest required)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi import HTTPException
from starlette.requests import Request
from mcp_canarytrap.cve_2026_5029 import enforce_cve_2026_5029_request


def make_request(headers):
    scope = {
        "type": "http", "method": "POST", "path": "/gateway/demo",
        "headers": [(key.lower().encode(), value.encode()) for key, value in headers.items()],
        "query_string": b"", "server": ("localhost", 8000), "scheme": "http",
        "client": ("127.0.0.1", 12345), "http_version": "1.1",
    }
    return Request(scope)


def expect_status(label, headers, expected):
    try:
        enforce_cve_2026_5029_request(make_request(headers))
    except HTTPException as exc:
        actual = exc.status_code
    else:
        actual = 200
    if actual != expected:
        raise SystemExit(f"FAIL {label}: expected {expected}, got {actual}")
    print(f"PASS {label}: HTTP {actual}")


def main():
    os.environ["CANARYTRAP_CVE_2026_5029_MODE"] = "true"
    os.environ["CANARYTRAP_CVE_ALLOWED_HOSTS"] = "localhost"
    os.environ["CANARYTRAP_CVE_ALLOWED_ORIGINS"] = "http://localhost:8000"
    os.environ["CANARYTRAP_RBAC_KEYS"] = (
        '{"examiner-demo-key":{"tenant":"examiner-demo","role":"operator"}}'
    )

    expect_status("missing API key", {"host": "localhost:8000"}, 401)
    expect_status("invalid API key", {
        "host": "localhost:8000", "x-canarytrap-api-key": "wrong"
    }, 403)
    expect_status("untrusted Host", {
        "host": "attacker.example", "x-canarytrap-api-key": "examiner-demo-key"
    }, 400)
    expect_status("untrusted Origin", {
        "host": "localhost:8000", "origin": "https://attacker.example",
        "x-canarytrap-api-key": "examiner-demo-key"
    }, 403)

    result = enforce_cve_2026_5029_request(make_request({
        "host": "localhost:8000", "origin": "http://localhost:8000",
        "x-canarytrap-api-key": "examiner-demo-key",
    }))
    if result != "examiner-demo":
        raise SystemExit(f"FAIL valid request: unexpected tenant {result!r}")
    print("PASS valid credentials + allowed Host/Origin: tenant examiner-demo")
    print("All manual CVE-profile checks passed.")


if __name__ == "__main__":
    main()
