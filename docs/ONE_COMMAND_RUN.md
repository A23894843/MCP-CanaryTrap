# One-command startup

## First-time setup (once per machine)
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Every subsequent run — one command
From the project folder:
```bash
source .venv/bin/activate && python run.py
```

Open `http://127.0.0.1:8000/dashboard`.

The integrated dashboard provides:
- Module 1 safe vulnerable-flow simulation.
- Module 2 local dependency/config auditor.
- Module 3 runtime OAuth URL policy validator.
- Module 4 decoy monitoring and SQLite event history.

The instrumented MCP STDIO server remains available to external MCP hosts through `app/mcp_server.py`; an MCP host that uses STDIO must launch that server as a separate protocol process. The one-command launcher starts the integrated assessment dashboard and all HTTP-accessible modules. It does not impersonate an external MCP host or merge two incompatible server lifecycles.
