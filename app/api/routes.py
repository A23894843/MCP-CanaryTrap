from fastapi import APIRouter, Header, HTTPException
from app.core.detector import detect_interaction
from app.core.decoys import get_decoys
from app.core.evidence import append_evidence, verify_evidence_chain
from app.core.cve_guard import check_gateway_request, cve_metadata
from app.storage.database import save_event, get_all_events, get_evidence_summary

router = APIRouter()

@router.get("/decoys")
def show_decoys():
    return get_decoys()

@router.post("/inspect")
def inspect_target(target_name: str):
    result = detect_interaction(target_name)
    event_type = "DECOY_ACCESS" if result["detected"] else "NORMAL_INTERACTION"
    save_event(result["target"], event_type, result["message"])
    append_evidence(event_type, result["target"], result["verdict"],
                    {"trigger": result["trigger"]})
    return result

@router.get("/events")
def show_events():
    return get_all_events()

@router.get("/api/cve")
def cve_info():
    return cve_metadata()

@router.post("/api/cve/guard-check")
def cve_guard_check(
    authorization: str | None = Header(default=None),
    host: str | None = Header(default=None),
    origin: str | None = Header(default=None),
):
    token = authorization[7:].strip() if authorization and authorization.startswith("Bearer ") else None
    decision = check_gateway_request(token, host, origin)
    event_type = "CVE_GATEWAY_ALLOWED" if decision["allowed"] else "CVE_GATEWAY_BLOCKED"
    save_event("CVE-2026-5029", event_type, decision["reason"])
    append_evidence(event_type, "CVE-2026-5029",
                    "ACCEPTED" if decision["allowed"] else "BLOCKED",
                    {"status_code": decision["status_code"], "host": host, "origin": origin})
    if not decision["allowed"]:
        raise HTTPException(status_code=decision["status_code"], detail=decision["reason"])
    return {"decision": "ACCEPTED", "cve": "CVE-2026-5029", "message": decision["reason"],
            "note": "This is the prototype's request-boundary demonstration endpoint."}

@router.get("/api/evidence")
def evidence_summary():
    return get_evidence_summary()

@router.get("/api/evidence/verify")
def evidence_verify():
    return verify_evidence_chain()
