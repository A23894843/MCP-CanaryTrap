"""Typed audit events shared by the harness, persistence layer and verdict engine."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
import json
import uuid

@dataclass(frozen=True)
class InteractionEvent:
    """One observed operation in a test session."""
    session_id: str
    operation: str
    target: str
    target_kind: str
    is_decoy: bool
    timestamp: str
    details: str = ""
    event_id: str = ""

    @classmethod
    def create(cls, session_id: str, operation: str, target: str, target_kind: str,
               is_decoy: bool, details: str = "") -> "InteractionEvent":
        """Build an event with a UTC timestamp and unique identifier."""
        return cls(session_id, operation, target, target_kind, is_decoy,
                   datetime.now(timezone.utc).isoformat(), details, str(uuid.uuid4()))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary for API responses and reports."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize the event deterministically for storage/export."""
        return json.dumps(self.to_dict(), sort_keys=True)
