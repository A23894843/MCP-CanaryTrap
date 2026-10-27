# 07 — Phase 1 Code Walkthrough

This document explains the Phase 1 implementation file by file and identifies the boundary handed to Phase 2.

## `src/mcp_canarytrap/server.py`

The educational MCP server. It exposes the MCP primitives that the team must understand before building the security harness.

- `mcp`: the MCP server instance.
- `EMPLOYEES`: fabricated in-memory data; no real sensitive data is used.
- `search_employee(employee_id)`: MCP Tool demonstrating an action.
- `list_departments()`: MCP Tool demonstrating another callable capability.
- `employee_profile(employee_id)`: Resource Template at `employee://profile/{employee_id}`.
- `company_departments()`: direct Resource at `company://departments`.
- `find_employee(employee_id)`: MCP Prompt demonstrating prompt retrieval.
- `mcp.run()`: starts the server and its configured transport.

This file is a learning/reference server, not the server-under-test and not the final decoy injector.

## `src/mcp_canarytrap/client.py`

The learning MCP client. It launches the server as a subprocess over stdio and demonstrates the normal client lifecycle.

Flow:

```text
create server parameters
        ↓
start MCP server subprocess
        ↓
establish client session
        ↓
inspect server information/capabilities
        ↓
list tools/resources/templates/prompts
        ↓
call a tool
        ↓
read a resource
        ↓
get a prompt
        ↓
close session
```

This gives Phase 2 a concrete understanding of where runtime interactions occur.

## `src/mcp_canarytrap/phase1_design.py`

The first CanaryTrap design model. It does not yet inject live decoys.

### `DecoyCategory`
The three categories proposed for Phase 1:

1. `HIGH_PRIVILEGE_TOOL`
2. `SENSITIVE_DATA_ASSET`
3. `HIGH_VALUE_RECORD`

### `Decoy`
A small immutable data object containing category, name, description, and whether legitimate access is allowed.

### `PlacementPlan`
Stores the session ID and ordered decoys for that session.

### `build_phase1_decoys()`
Creates safe fabricated examples representing the three categories. They are design objects, not real credentials or destructive operations.

### `deterministic_seed(session_id)`
Uses SHA-256-derived bytes to turn a session identifier into a reproducible integer seed.

### `create_placement_plan(session_id)`
Shuffles the Phase 1 decoy list using the session-derived seed. The same session produces the same plan. This is a scaffold for research, not proof of fingerprinting resistance.

## `tests/test_phase1.py`

The tests verify three things:

1. all three decoy categories exist;
2. placement is reproducible for the same session ID;
3. the MCP server exposes and executes the expected tools/resources/prompt.

Run:

```bash
python -m pytest -v
```

## Why Phase 1 stops here

The project plan puts the sandbox harness, decoy generator and interaction logger after the MCP/decoy-design phase. The deterministic verdict engine and evidence reporting come later. Therefore Phase 1 deliberately does not contain those components.
