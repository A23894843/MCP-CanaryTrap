"""Tamper-evident event ledger for examiner-verifiable incident evidence."""
import hashlib
import json
from app.storage.database import get_last_evidence_hash, save_evidence_record, get_evidence_records

GENESIS = "0" * 64

def append_evidence(event_type: str, target: str, verdict: str, details: dict | None = None) -> dict:
    previous = get_last_evidence_hash() or GENESIS
    payload = {
        "event_type": event_type,
        "target": target,
        "verdict": verdict,
        "details": details or {},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
    save_evidence_record(payload, previous, digest)
    return {"previous_hash": previous, "event_hash": digest, **payload}

def verify_evidence_chain() -> dict:
    records = get_evidence_records()
    previous = GENESIS
    checked = 0
    for row in records:
        record_id, payload_json, stored_previous, stored_hash = row
        if stored_previous != previous:
            return {"valid": False, "checked": checked, "broken_at": record_id,
                    "reason": "Previous-hash mismatch"}
        canonical = json.dumps(json.loads(payload_json), sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False)
        expected = hashlib.sha256((previous + canonical).encode("utf-8")).hexdigest()
        if expected != stored_hash:
            return {"valid": False, "checked": checked, "broken_at": record_id,
                    "reason": "Record hash mismatch"}
        previous = stored_hash
        checked += 1
    return {"valid": True, "checked": checked, "head_hash": previous,
            "message": "Evidence chain integrity verified."}
