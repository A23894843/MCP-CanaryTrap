# MCP-CanaryTrap

**A deterministic decoy-access detection prototype for Model Context Protocol (MCP) server testing.**

> Academic demonstration only. The current harness simulates MCP-like interactions. It does not transparently monitor arbitrary third-party MCP servers and is not a production security product.

## What it demonstrates
- MCP SDK learning server/client with tools, resources, a resource template and a prompt.
- Three fictional decoy categories: high-privilege tool, sensitive-data asset and high-value record.
- Reproducible per-session decoy placement scaffold.
- Controlled benign and overreaching scenarios.
- Timestamped interaction events persisted in SQLite.
- Deterministic verdict: `CLEAN` with no recorded decoy access, `FLAGGED` with one or more decoy accesses.
- Evidence event IDs, FastAPI reporting endpoints and a browser dashboard.
- Automated regression tests and presentation documentation.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -v
```

Run the command-line demo:

```bash
python -m mcp_canarytrap.demo --scenario both
```

Run the dashboard:

```bash
python -m mcp_canarytrap.api
```

Open `http://127.0.0.1:8000`; API documentation is at `http://127.0.0.1:8000/docs`.

## Project map

```text
src/mcp_canarytrap/
├── server.py          # MCP SDK learning server
├── client.py          # MCP SDK learning client
├── phase1_design.py   # Decoy taxonomy and placement
├── events.py          # Interaction event model
├── harness.py         # Controlled scenario execution
├── verdict.py         # Deterministic CLEAN/FLAGGED policy
├── storage.py         # SQLite persistence
├── demo.py            # CLI demo
├── api.py             # FastAPI endpoints
└── templates/index.html
                       # Browser dashboard

tests/
├── test_phase1.py
└── test_detection_pipeline.py

docs/                  # Setup, architecture, code walkthrough, test plan,
                       # threat model, limitations, sources, viva and handoff
```

## Demo expectations
| Scenario | Expected verdict | Evidence |
|---|---|---|
| `benign` | `CLEAN` | 0 decoy event IDs |
| `overreaching` | `FLAGGED` | 3 decoy event IDs |

These are outcomes of the scripted simulation, not measured real-world detection rates.

## Documentation order
1. `docs/00-project-overview.md`
2. `docs/01-setup-and-run.md`
3. `docs/02-architecture.md`
4. `docs/03-code-walkthrough.md`
5. `docs/04-test-plan-and-results.md`
6. `docs/05-threat-model-and-safety.md`
7. `docs/06-limitations-and-real-integration.md`
8. `docs/07-viva-and-demo-script.md`
9. `docs/08-sources.md`
10. `docs/09-team-handoff.md`

## Docker

```bash
docker compose up --build
```

The service is bound to localhost. The container persists its SQLite data in a named volume.

## Important research limitation
The demo harness generates controlled events internally. The MCP SDK example server/client are real local MCP demonstrations but are not yet wired to the harness as a live traffic observer. A transport-aware adapter/proxy, actual sandbox isolation and independent evaluation corpus are needed for a stronger research claim. See `docs/06-limitations-and-real-integration.md`.
