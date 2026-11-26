"""Manual, dependency-light verification of core project logic."""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Use a temporary isolated SQLite database for this verification.
tmp = tempfile.TemporaryDirectory()
os.environ["CANARYTRAP_TEST_DB"] = str(Path(tmp.name) / "verify.db")

# database.py resolves the path at import time, so patch it before imports.
from app.storage import database
database.DATABASE_PATH = Path(os.environ["CANARYTRAP_TEST_DB"])
database.create_database()

from app.core.detector import detect_interaction
from app.core.evidence import append_evidence, verify_evidence_chain
from app.core.cve_guard import check_gateway_request

def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print("[PASS]", message)

check(detect_interaction("system_secrets")["verdict"] == "FLAGGED",
      "configured decoy returns FLAGGED")
check(detect_interaction("SYSTEM_SECRETS")["verdict"] == "FLAGGED",
      "matching is case-insensitive")
check(detect_interaction("weather_search")["verdict"] == "CLEAN",
      "normal tool returns CLEAN")

os.environ["CANARYTRAP_CVE_TOKEN"] = "local-demo-secret"
os.environ["CANARYTRAP_ALLOWED_HOSTS"] = "localhost,127.0.0.1"
os.environ["CANARYTRAP_ALLOWED_ORIGINS"] = "http://localhost:8000"
check(check_gateway_request(None, "localhost:8000", None)["status_code"] == 401,
      "missing bearer token is rejected")
check(check_gateway_request("wrong", "localhost:8000", None)["status_code"] == 403,
      "invalid bearer token is rejected")
check(check_gateway_request("local-demo-secret", "evil.example", None)["status_code"] == 400,
      "unapproved Host is rejected")
check(check_gateway_request("local-demo-secret", "localhost:8000",
                            "https://evil.example")["status_code"] == 403,
      "unapproved Origin is rejected")
check(check_gateway_request("local-demo-secret", "localhost:8000",
                            "http://localhost:8000")["allowed"],
      "valid request passes the guard")

append_evidence("DECOY_ACCESS", "system_secrets", "FLAGGED", {"trigger": "EXACT_DECOY_NAME_MATCH"})
append_evidence("CVE_GATEWAY_BLOCKED", "CVE-2026-5029", "BLOCKED", {"status_code": 401})
check(verify_evidence_chain()["valid"], "SHA-256 evidence chain verifies")
with database._connect() as conn:
    conn.execute("UPDATE evidence_chain SET payload_json=? WHERE id=1",
                 ('{"event_type":"ALTERED","target":"x","verdict":"CLEAN","details":{}}',))
check(not verify_evidence_chain()["valid"], "tampered evidence payload is detected")
print("All manual verification checks passed.")
tmp.cleanup()
