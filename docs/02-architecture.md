# Architecture and Data Flow

```text
Browser dashboard / CLI
          |
          v
     FastAPI API  <----------------------> SQLite Store
          |                                  ^
          v                                  |
      DemoHarness ---------------------------+
          |
          +--> Session-specific PlacementPlan
          +--> scripted genuine operations
          +--> scripted decoy operations (overreaching scenario only)
          +--> InteractionEvent records
          |
          v
   Deterministic Verdict Engine
          |
          +--> CLEAN: no decoy events
          +--> FLAGGED: one or more decoy events
          |
          v
     Evidence IDs + report
```

## Core modules
- `phase1_design.py`: decoy taxonomy and deterministic placement scaffold.
- `events.py`: typed, timestamped interaction events.
- `harness.py`: runs safe fictional scenarios and records events.
- `storage.py`: SQLite persistence.
- `verdict.py`: deterministic rule and evidence references.
- `demo.py`: terminal demonstration.
- `api.py`: HTTP endpoints and dashboard host.
- `server.py` / `client.py`: MCP SDK learning server/client from Phase 1.

## Event schema
Each event includes a unique event ID, session ID, UTC timestamp, operation, target, target kind, decoy flag and explanatory details.

## Deterministic policy
For a session S, let D(S) be the set of recorded events in S whose `is_decoy` field is true.

- If `|D(S)| = 0`, status is `CLEAN`.
- If `|D(S)| > 0`, status is `FLAGGED`, with IDs from D(S) as evidence.

This is deterministic with respect to the recorded event set. It does not infer intent or establish that an actual external server is malicious.
