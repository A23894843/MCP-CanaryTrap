from app.core.decoys import get_decoy
def detect_interaction(target_name):
    decoy = get_decoy(target_name)
    if decoy:
        return {"detected": True, "target": target_name, "severity": decoy["severity"],
                "event_type": "DECOY_ACCESS",
                "message": f"Configured decoy tool '{target_name}' was accessed."}
    return {"detected": False, "target": target_name, "severity": "INFO",
            "event_type": "NORMAL_ACTIVITY",
            "message": f"No configured decoy matched '{target_name}'."}
