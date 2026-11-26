# MCP-CanaryTrap

**Research direction:** A deterministic decoy-injection mechanism for detecting overreaching behavior in Model Context Protocol (MCP) servers.

**CVE case study:** [CVE-2025-6514 — NVD record](https://nvd.nist.gov/vuln/detail/CVE-2025-6514) · [GitHub Security Advisory](https://github.com/advisories/GHSA-6xpm-ggf7-wc3p) · [JFrog technical analysis](https://research.jfrog.com/vulnerabilities/mcp-remote-command-injection-rce-jfsa-2025-001290844/)

Deterministic decoy-monitoring proof of concept for an instrumented Model Context Protocol (MCP) server. The research proposal is to use fabricated resources with no legitimate role in a controlled task as binary signals of overreaching behavior.

## Features
- MCP server exposes `weather_search` plus fictional decoys: `admin_config`, `customer_backup`, `system_secrets`.
- Exact-name rule-based detection; HIGH / CRITICAL severity policy.
- SQLite event persistence with timestamp and event source.
- FastAPI monitoring API and browser dashboard.
- Interactive Python MCP client.
- No AI/ML and no pytest dependency.

## Setup (Kali/Linux)
From the project root:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```
If `venv` is unavailable, install your distribution's `python3-venv` package.

## Run dashboard
Terminal 1:
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/dashboard`; API docs are at `/docs`.

## Run MCP client
Terminal 2, from the project root:
```bash
source .venv/bin/activate
python -m app.mcp_client
```
Choose a listed tool. `weather_search` should not create a decoy event. Each decoy tool should create a record.

## Manual verification
Use the dashboard to see the latest events. Or inspect the database:
```bash
sqlite3 data/canarytrap.db
```
```sql
.headers on
.mode column
SELECT id,target_name,event_type,severity,source,timestamp
FROM security_events ORDER BY id DESC LIMIT 20;
.quit
```
No automated test framework is required; document actual manual results and capture screenshots.

## API
- `GET /` — service information
- `GET /health` — health check
- `GET /api/decoys` — configured decoys
- `POST /api/inspect?target_name=admin_config` — manual HTTP inspection
- `GET /api/events` — event history
- `GET /api/stats` — summary counts
- `GET /docs` — interactive API documentation

## Architecture / scope
MCP client -> instrumented MCP server -> detector -> SQLite. FastAPI reads the database for the dashboard. The dashboard's manual inspection uses HTTP and is a separate path from MCP calls.

This prototype monitors only tool calls passing through its own instrumented MCP server. It does not passively monitor arbitrary third-party MCP servers or all network traffic. A decoy access is a suspicious signal, not proof of malicious intent. Decoys contain fictional content only. Keep the development server on localhost; production use would require authentication, authorization, secure transport, and hardened logging.

## Troubleshooting
- Run commands from the project root with `.venv` active.
- `CallToolResult` uses `result.is_error` (not `isError`).
- MCP STDIO stdout is protocol data. Do not use ordinary `print()` statements in the server or startup imports; send diagnostics to stderr.
- If the SDK's installed API differs, check the installed MCP SDK version. This project follows the `MCPServer` decorator API used in the development environment.


## CVE-2025-6514 assessment modules

The project title remains **MCP-CanaryTrap**. The CVE is the case study; this project is an assessment prototype, not an upstream patch.

### Module 1 — Safe vulnerable-flow simulation
```bash
python -m app.security.lab_simulator
```
This models an unsafe acceptance decision and writes `/tmp/mcp-canarytrap-simulation.txt`. It never executes a shell command or launches a browser.

### Module 2 — Local dependency and configuration auditor
```bash
python -m app.security.security_cli .
python -m app.security.security_cli --json ~/Desktop
```
Supply project directories, npm cache directories, or exact config/manifest files. The scanner checks package manifests, lockfiles and MCP config references. A config-only match cannot establish the actual installed package version; verify resolution manually.

### Module 3 — Runtime URL policy validator
With FastAPI running, open `/docs` and call:
`POST /api/security/validate-authorization-endpoint`
with JSON:
```json
{"authorization_endpoint":"https://login.example.org/oauth/authorize"}
```
Unsafe or non-HTTPS endpoints are rejected by the policy.

### CVE case-study documentation
See `docs/CVE-2025-6514_CASE_STUDY.md` and `docs/THREE_MODULES.md`.

**Safety and scope:** The included lab is a safe simulation, not a live exploit. The URL validator is a defensive policy example, not a replacement for the patched upstream client. Use `mcp-remote` 0.1.16 or later; do not rely on this project as the sole protection for third-party clients.


## One-command integrated startup

First-time setup:
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Every later launch (from the project root):
```bash
source .venv/bin/activate && python run.py
```

Open `http://127.0.0.1:8000/dashboard`. The integrated dashboard runs the safe CVE-flow simulator, local auditor, OAuth URL validator, and decoy monitor from one interface. See `docs/ONE_COMMAND_RUN.md`.

Note: the MCP STDIO server is still available for external MCP clients, which must launch it as their own protocol process. The single command starts the complete integrated assessment dashboard; it cannot replace the MCP host process.


## Synopsis alignment: implemented scope vs. research objectives

The official synopsis defines five research objectives: (1) a decoy taxonomy, (2) a placement strategy that preserves legitimate task behavior and resists fingerprinting, (3) deterministic detection and verdicts, (4) evasion resistance, and (5) evaluation against legitimate and deliberately misbehaving MCP servers.

### Implemented in this repository
- A taxonomy of 30 fictional decoy tool names in the instrumented MCP server.
- Deterministic exact-name matching; a configured decoy match creates a structured event.
- SQLite event persistence and a FastAPI dashboard for reviewing events.
- Supporting CVE-2025-6514 utilities: safe vulnerable-flow simulation, local dependency/configuration audit, and authorization-endpoint URL policy validation.
- Manual demonstration paths for a positive decoy case and a normal-tool negative case.

### Research work not yet established
- General-purpose injection/placement of decoys into arbitrary third-party MCP server sessions.
- Evidence that decoys are statistically indistinguishable from genuine assets.
- Resistance to fingerprinting or deliberate decoy avoidance.
- A formal multi-server evaluation dataset and measured false-positive/detection rates.

Do not describe these proposed properties as completed results. A decoy match is a deterministic observation within the instrumented environment; it is not, by itself, proof of malicious intent. This prototype does not passively monitor arbitrary third-party MCP servers.

## CVE-2025-6514 references
- [NVD vulnerability record](https://nvd.nist.gov/vuln/detail/CVE-2025-6514)
- [GitHub Security Advisory](https://github.com/advisories/GHSA-6xpm-ggf7-wc3p)
- [JFrog technical analysis](https://research.jfrog.com/vulnerabilities/mcp-remote-command-injection-rce-jfsa-2025-001290844/)

## Deployed Project
- [Live deployed project on Render](https://mcp-canarytrap.onrender.com/)

CVE-2025-6514 concerns OS command injection in affected `mcp-remote` versions when connecting to untrusted MCP servers using crafted OAuth `authorization_endpoint` metadata. The affected range is 0.0.5 through 0.1.15; 0.1.16 is the fixed version. This project is a supporting educational assessment prototype, not an upstream patch or a live exploit reproduction.
