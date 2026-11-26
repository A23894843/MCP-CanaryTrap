from .decoys import get_decoys

def detect_interaction(target_name: str) -> dict:
    """Deterministically flag exact configured decoy names (case-insensitive)."""
    normalized = (target_name or "").strip().casefold()
    decoys = {item["name"].casefold(): item for item in get_decoys()}
    match = decoys.get(normalized)
    if match:
        return {
            "detected": True,
            "verdict": "FLAGGED",
            "target": match["name"],
            "message": "Configured decoy interaction detected.",
            "trigger": "EXACT_DECOY_NAME_MATCH",
        }
    return {
        "detected": False,
        "verdict": "CLEAN",
        "target": (target_name or "").strip(),
        "message": "No configured decoy interaction detected.",
        "trigger": None,
    }
