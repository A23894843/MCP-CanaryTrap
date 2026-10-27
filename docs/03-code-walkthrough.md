# Code Walkthrough

## `phase1_design.py`
`DecoyCategory` defines three categories. `Decoy` describes a fictional decoy. `PlacementPlan` groups decoys for a session. `deterministic_seed()` hashes the session ID with SHA-256 rather than relying on Python's process-randomized `hash()`. `create_placement_plan()` shuffles decoys using a seeded local random generator. Same ID means same order; this is reproducibility, not cryptographic unpredictability.

## `events.py`
`InteractionEvent` is an immutable data model for an observed or simulated interaction. `create()` assigns UTC time and a UUID; `to_dict()` and `to_json()` support API output and exports.

## `harness.py`
`DemoHarness.run()` accepts `benign` or `overreaching`. Both scenarios record two genuine interactions. The overreaching scenario additionally records one event for each decoy category. The harness persists events and evaluates the session. This module simulates the observed operations; it is not a live proxy.

## `verdict.py`
`evaluate_session()` filters events to the requested session and checks the decoy flag. It emits `CLEAN` or `FLAGGED`, a reason, evaluation timestamp and event IDs for the evidence.

## `storage.py`
`Store` creates three SQLite tables: sessions, events and verdicts. It provides methods to create sessions, store events, persist verdicts and read session/event lists.

## `demo.py`
The CLI accepts `--scenario benign|overreaching|both` and a database path. It prints JSON, making the demo suitable for screenshots or terminal presentation.

## `api.py` and `templates/index.html`
The API exposes `/health`, `/api/sessions`, `/api/events`, and `POST /api/demo/{scenario}`. The root route serves the browser dashboard. The dashboard buttons call the API and render sessions, events and the latest evidence.

## `server.py` and `client.py`
These preserve the Phase 1 MCP SDK demonstration. They show actual MCP primitives in the local demo server/client lifecycle, but are separate from the simulated event harness in this version.
