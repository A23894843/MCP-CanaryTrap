from fastapi import APIRouter, HTTPException, Query
from app.core.decoys import get_decoys
from app.core.detector import detect_interaction
from app.storage.database import get_all_events, get_event_stats, save_event

router = APIRouter(prefix="/api", tags=["Monitoring API"])

@router.get("/decoys")
def list_decoys():
    return get_decoys()

@router.post("/inspect")
def inspect_target(target_name: str = Query(..., min_length=1, max_length=100)):
    target_name = target_name.strip()
    if not target_name:
        raise HTTPException(status_code=400, detail="target_name cannot be blank")
    result = detect_interaction(target_name)
    if result["detected"]:
        save_event(result["target"], result["event_type"], result["severity"],
                   result["message"], source="dashboard")
    return result

@router.get("/events")
def list_events(limit: int = Query(100, ge=1, le=500)):
    return get_all_events(limit)

@router.get("/stats")
def stats():
    return get_event_stats()
