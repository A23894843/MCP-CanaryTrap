# MCP-CanaryTrap — Phase 1

Educational implementation of Phase 1 from the project synopsis: learn MCP protocol/tool/resource schema and create the initial decoy taxonomy + placement design.

## Included
- Small MCP server: tools, resources, prompt
- MCP client over stdio
- Phase-1 decoy taxonomy and session-derived placement model
- Tests
- Study notes and viva questions

This is **not the final CanaryTrap system**. The sandbox harness, interaction logger, real decoy injection, verdict engine, dashboard and evaluation belong to later phases.

## Setup
Python 3.10+.

```text
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Linux/macOS
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the learning client:

```text
python -m mcp_canarytrap.client
```

Run tests:

```text
pytest
```

Study in order:
1. docs/01-mcp-fundamentals.md
2. docs/02-protocol-flow.md
3. docs/03-phase1-decoy-design.md
4. docs/04-phase1-exercises.md
5. docs/05-phase1-viva.md

Do not submit this as the final project. Modify it and understand every component.
