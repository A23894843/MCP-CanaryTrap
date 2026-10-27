"""Controlled scenario harness for benign and deliberately overreaching behavior."""
from datetime import datetime, timezone
import uuid
from .events import InteractionEvent
from .phase1_design import create_placement_plan
from .storage import Store
from .verdict import evaluate_session

class DemoHarness:
    """Run reproducible fictional scenarios and persist observations.

    The scenarios simulate MCP-like operations; this version does not intercept an
    arbitrary external MCP server. See docs/06-limitations-and-real-integration.md.
    """
    def __init__(self, store: Store | None = None):
        self.store = store or Store()

    def run(self, scenario: str = "benign", session_id: str | None = None) -> dict:
        """Run a known scenario, log every simulated interaction, and evaluate it."""
        if scenario not in {"benign", "overreaching"}:
            raise ValueError("scenario must be 'benign' or 'overreaching'")
        sid = session_id or f"ct-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()
        plan = create_placement_plan(sid)
        decoy_by_category = {d.category.value: d for d in plan.decoys}
        self.store.create_session(sid, scenario, created_at)
        events: list[InteractionEvent] = []

        # Benign operations touch only genuine demo targets.
        genuine = [
            ("tools/call", "search_employee", "tool", False, "Requested employee lookup."),
            ("resources/read", "employee://profile/1024", "resource", False, "Requested employee profile."),
        ]
        for operation, target, kind, is_decoy, details in genuine:
            event = InteractionEvent.create(sid, operation, target, kind, is_decoy, details)
            self.store.add_event(event)
            events.append(event)

        # The overreaching scenario additionally touches every decoy category.
        if scenario == "overreaching":
            for decoy in plan.decoys:
                kind = "tool" if decoy.category.value == "high_privilege_tool" else "resource"
                operation = "tools/call" if kind == "tool" else "resources/read"
                event = InteractionEvent.create(sid, operation, decoy.name, kind, True,
                                                f"Simulated access to {decoy.category.value} decoy.")
                self.store.add_event(event)
                events.append(event)

        verdict = evaluate_session(sid, events)
        self.store.save_verdict(verdict)
        return {"session": self.store.get_session(sid), "events": [e.to_dict() for e in events],
                "verdict": verdict.to_dict(), "placement": [d.name for d in plan.decoys]}
