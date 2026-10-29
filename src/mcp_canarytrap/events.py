# Annotated source file for MCP-CanaryTrap v1.3.2.
# Lines beginning with "Explanation:" describe the following statement or branch.
# Original executable statements are preserved; comments are for learning.

# Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
"""Typed audit events shared by the harness, persistence layer and verdict engine."""
# Explanation: Imports names from dataclasses.
from dataclasses import asdict, dataclass
# Explanation: Imports names from datetime.
from datetime import datetime, timezone
# Explanation: Imports names from typing.
from typing import Any
# Explanation: Imports modules that this file uses.
import json
# Explanation: Imports modules that this file uses.
import uuid

@dataclass(frozen=True)
# Explanation: Class InteractionEvent: groups related data and operations.
class InteractionEvent:
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    """One observed operation in a test session."""
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    session_id: str
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    operation: str
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    target: str
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    target_kind: str
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    is_decoy: bool
    # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
    timestamp: str
    # Explanation: Assigns or updates a value used later by this function or module.
    details: str = ""
    # Explanation: Assigns or updates a value used later by this function or module.
    event_id: str = ""

    @classmethod
    # Explanation: Function create: Build an event with a UTC timestamp and unique identifier.
    def create(cls, session_id: str, operation: str, target: str, target_kind: str,
               is_decoy: bool, details: str = "") -> "InteractionEvent":
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Build an event with a UTC timestamp and unique identifier."""
        # Explanation: Return this result to the caller; this ends the current function path.
        return cls(session_id, operation, target, target_kind, is_decoy,
                   datetime.now(timezone.utc).isoformat(), details, str(uuid.uuid4()))

    # Explanation: Function to_dict: Return a JSON-compatible dictionary for API responses and reports.
    def to_dict(self) -> dict[str, Any]:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Return a JSON-compatible dictionary for API responses and reports."""
        # Explanation: Return this result to the caller; this ends the current function path.
        return asdict(self)

    # Explanation: Function to_json: Serialize the event deterministically for storage/export.
    def to_json(self) -> str:
        # Explanation: Executes this statement. Follow the variables and called functions to understand its input, side effects, and result.
        """Serialize the event deterministically for storage/export."""
        # Explanation: Return this result to the caller; this ends the current function path.
        return json.dumps(self.to_dict(), sort_keys=True)
