# Demonstration and Viva Notes

## Suggested 5-minute demo
1. Introduce the project and its scope.
2. Start `uvicorn app.main:app --reload`.
3. Open `http://127.0.0.1:8000/dashboard`.
4. Run `python -m app.mcp_client` in another terminal.
5. Call `weather_search` and show no decoy event.
6. Run client again; call `admin_config`; show HIGH event in dashboard.
7. Call `customer_backup` or `system_secrets`; show CRITICAL event.
8. Show `/docs` and explain the API.

## Viva questions
**What is MCP?** A protocol for connecting an AI application/client with tools and resources through a standardized interface.

**What is a decoy tool?** A deliberately fictional tool used as a monitoring signal when invoked.

**What does the detector do?** Exact-name matching against the configured decoy list.

**Does it use AI or ML?** No. Detection is deterministic and rule-based.

**Why SQLite?** Lightweight, file-based persistence suitable for a local prototype.

**Why FastAPI?** It provides HTTP endpoints, validation, and interactive API documentation.

**Does a decoy call prove an attack?** No. It is a suspicious signal requiring investigation.

**Does it monitor all MCP servers?** No. It monitors only calls through this project's instrumented MCP server.

**Why keep stdout clean?** MCP STDIO uses stdout for protocol messages; extra output can break JSON-RPC communication.

**Future improvements?** Authentication, alert integrations, configurable policies, audit export, and tamper-evident storage.

## Before submission
- Run all manual checks on your own machine.
- Capture genuine screenshots of dashboard, client, decoy detection, and event records.
- Add your actual student / department / guide details to your institution's cover page.
- Be prepared to explain the limitations honestly.
