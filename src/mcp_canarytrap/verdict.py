"""Deterministic verdict policy: any recorded decoy touch flags a session."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from .events import InteractionEvent

@dataclass(frozen=True)
class Verdict:
    """A verdict and its evidence references."""
    session_id: str
    status: str
    reason: str
    evidence_event_ids: tuple[str, ...]
    evaluated_at: str

    def to_dict(self) -> dict:
        """Convert tuple fields into JSON-compatible lists."""
        result = asdict(self)
        result["evidence_event_ids"] = list(self.evidence_event_ids)
        return result

def evaluate_session(session_id: str, events: list[InteractionEvent]) -> Verdict:
    """Return FLAGGED iff at least one event marks an observed decoy access.

    This rule is deterministic given the same event set. It does not prove intent;
    it reports that a configured decoy was accessed during the test session.
    """
    decoy_events = [event for event in events if event.session_id == session_id and event.is_decoy]
    status = "FLAGGED" if decoy_events else "CLEAN"
    reason = (f"Observed {len(decoy_events)} decoy interaction(s)." if decoy_events
              else "No decoy interactions were recorded in this session.")
    return Verdict(session_id, status, reason, tuple(e.event_id for e in decoy_events),
                   datetime.now(timezone.utc).isoformat())
