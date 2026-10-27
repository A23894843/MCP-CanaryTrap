# Team Handoff Checklist

## Current deliverables
- [x] Phase 1 MCP server/client demonstration.
- [x] Three-category fictional decoy taxonomy.
- [x] Session-derived reproducible placement.
- [x] Simulated interaction logger and SQLite persistence.
- [x] Deterministic verdict engine with evidence references.
- [x] CLI demonstration for benign and overreaching scenarios.
- [x] FastAPI endpoints and browser dashboard.
- [x] Automated tests, setup guide, architecture, threat model, limitations and viva script.

## Before presentation
- [ ] Create a fresh virtual environment and install from `pyproject.toml`.
- [ ] Run `python -m pytest -v` and save the real output.
- [ ] Run both CLI scenarios and inspect the JSON evidence.
- [ ] Start dashboard and test both buttons.
- [ ] Capture screenshots from your own environment.
- [ ] Replace no claims with fabricated measurements; only report measured results.
- [ ] Ensure the repository excludes virtual environments, bytecode, databases and tokens.

## Phase 2/next research work
The simulation demonstrates the pipeline, but live transport observation and real sandboxing remain required before claiming end-to-end detection against external MCP servers.
