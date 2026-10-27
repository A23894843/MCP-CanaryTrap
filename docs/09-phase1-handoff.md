# 09 — Phase 1 → Phase 2 Handoff

## Status: COMPLETE

Phase 1 is complete when the repository demonstrates:

- MCP client/server foundation
- tools, resources, resource templates and prompts
- working stdio communication
- initial three-category decoy taxonomy
- session-derived placement scaffold
- tests and documentation

The verified command is:

```bash
python -m pytest -v
```

The learning demonstration is:

```bash
python -m mcp_canarytrap.client
```

## Phase 2 responsibilities

Build the next layer without discarding the Phase 1 concepts:

### 1. Sandbox harness
Run an MCP server under controlled isolation.

### 2. Decoy generator
Turn the Phase 1 decoy concepts into session-specific test resources/capabilities.

### 3. Interaction logger
Capture enough evidence to identify the MCP operation, target, timestamp/session, and whether the target is a decoy.

### 4. Server-under-test adapter
Provide a clean interface so different MCP server implementations can be tested without rewriting the harness.

## Do not assume

The current placement strategy is **not** experimentally proven to resist fingerprinting. Phase 2 should investigate metadata, names, schemas, ordering and cross-session patterns.

## Do not add yet

Do not jump directly to ML anomaly detection. The synopsis specifies a deterministic mechanism; the observation pipeline should be established first.

## Handoff checklist

- [ ] Run `python -m pytest -v`
- [ ] Run `python -m mcp_canarytrap.client`
- [ ] Read `07-code-walkthrough.md`
- [ ] Read `08-phase1-architecture.md`
- [ ] Understand all three decoy categories
- [ ] Understand the Phase 1 → Phase 2 boundary

## Files that must not be committed

```text
.venv/
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
```
