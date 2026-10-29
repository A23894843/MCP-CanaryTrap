# MCP-CanaryTrap v1.3.2

## Beginner-friendly dashboard (v1.3.2)

The dashboard has been redesigned with plain-language navigation, a guided first-use panel, clearer descriptions for tests and results, a lighter high-contrast visual style, and a matching sign-in/setup screen. The advanced gateway and protection settings remain available; they are explicitly described as advanced features.

**Suggested first run:** open **Try an Example**, run the normal example, then run the warning example, and open **Activity & Findings** to compare the results. A clean result only describes the inputs processed by that test; it is not a guarantee that an entire external system is safe.
**A deterministic decoy-access research prototype for Model Context Protocol (MCP) server testing, with deployment configuration tooling.**

> Important scope statement: the project now includes real-message monitoring adapters for configured Streamable HTTP and local stdio MCP connections, plus simulation mode. It is a research prototype, not a universal transparent proxy or an industry-validated security product. Validate every target server/client combination before operational use.

## What it demonstrates
- MCP SDK learning server/client with tools, resources, a resource template and a prompt.
- Three fictional decoy categories: high-privilege tool, sensitive-data asset and high-value record.
- Reproducible per-session decoy placement scaffold.
- Controlled benign and overreaching scenarios.
- Examiner-defined custom test builder: configure decoy target names and structured interactions in the dashboard; the backend derives decoy matches and evaluates the same verdict rule without adding a new hardcoded scenario.
- Timestamped interaction events persisted in SQLite.
- Deterministic verdict: `CLEAN` with no recorded decoy access, `FLAGGED` with one or more decoy accesses.
- Evidence event IDs, FastAPI reporting endpoints and a browser dashboard. In production mode, browser users sign in with a dashboard account (created during first-run setup if environment credentials are not configured); HTTP Basic remains available for compatible API clients. `/health` and `/ready` are health endpoints.
- Automated regression tests and presentation documentation.
- **Security Center (non-AI/ML):** tenant-scoped allow/deny/monitor policies enforced for supported tool calls, resource reads and prompt gets on HTTP/stdio gateway traffic; maintained MCP inventory; configured-connection reconciliation; posture checks; policy smoke tests; deterministic frequency baselines; cross-server exact-match correlation; unregistered observed gateway connection checks; webhook notifications; compliance-style posture report; role-based API keys; and SHA-256 hash-chained gateway audit entries.

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

The app now defaults to protected mode. Open `http://127.0.0.1:8000`; on first launch, create the administrator account in the browser. Use a unique password of at least 16 characters. API documentation is at `http://127.0.0.1:8000/docs` after sign-in. For a private local development session without login, explicitly set `APP_ENV=development` before starting the app; do not use that mode on a shared or public network. The dashboard has nine navigation views: **Home**, **Run a Test**, **Test History**, **Activity & Findings**, **Try an Example**, **Connect a Server**, **Protection Rules**, **Help & How It Works**, and **Settings & Deployment**. Start with **Try an Example**, then review **Activity & Findings**. The setup page creates an environment file and checklist locally in your browser; it does not deploy until you push the repository and authorize your hosting provider. Advanced server and protection settings are labelled as such.

## Project map

```text
src/mcp_canarytrap/
├── server.py          # MCP SDK learning server
├── client.py          # MCP SDK learning client
├── phase1_design.py   # Decoy taxonomy and placement
├── events.py          # Interaction event model
├── harness.py         # Built-in and examiner-defined scenario execution
├── verdict.py         # Deterministic CLEAN/FLAGGED policy
├── storage.py         # SQLite persistence
├── demo.py            # CLI demo
├── api.py             # FastAPI endpoints and connection setup
├── gateway_core.py    # Shared JSON-RPC decoy logic and evidence recorder
├── http_gateway.py    # Streamable HTTP MCP reverse proxy
├── stdio_proxy.py     # Local stdio MCP process wrapper
├── security_center.py # Policy, inventory, RBAC, audit, baselines, reports
└── templates/index.html
                       # Browser dashboard, setup wizard and Security Center
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
11. `docs/11-multipage-dashboard.md`
12. `docs/12-deployment-and-configuration.md`
13. `docs/13-live-gateway.md`
14. `docs/14-security-center.md`

## Deployment setup

### Local Docker (production-mode access guard)

```bash
cp .env.example .env
# Edit .env and set a unique DASHBOARD_PASSWORD (16+ characters).
docker compose up --build -d
```

Open `http://127.0.0.1:8000`. If dashboard credentials are not configured, create the first administrator in the setup form. The password is stored as a salted scrypt hash in the persistent SQLite database; the setup endpoint becomes unavailable after the first account is created. For a public deployment, configure environment credentials first or complete first-run setup in a controlled window, because the first visitor could otherwise claim the setup. Later visits use the dashboard sign-in form. Existing environment-configured `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` values and HTTP Basic clients remain supported. The service is bound to localhost and persists SQLite data in a named volume. Do not commit `.env`.

### Hosted Render Blueprint

A `render.yaml` Blueprint is included. Push the project to GitHub, then use the **Setup & Deploy** dashboard page to prepare the steps and open the Render Blueprint flow. Review the persistent-disk costs before deploying. After deployment, open the service URL and create the first administrator if dashboard credentials were not configured as environment variables. The administrator record is stored in the persistent disk-backed SQLite database. Alternatively, configure both `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` as secret environment variables. See [`docs/12-deployment-and-configuration.md`](docs/12-deployment-and-configuration.md).

The Setup & Deploy wizard runs locally in the browser and downloads `.env.production` and a deployment checklist. The Live MCP Gateway form saves non-secret upstream configuration to SQLite or generates a configuration snippet; it does not submit or store bearer-token values. Put secrets into the hosting provider's secret settings. The production dashboard supports a first-run administrator setup form and session-cookie sign-in; environment-configured HTTP Basic authentication remains supported for API clients. This is not enterprise SSO or a security certification.

## Custom test mode

The multi-page dashboard supports custom test cases through a structured form on the Custom Test Lab page. Enter a case name and description, add decoy target identifiers one per row, then add one or more observed interactions (operation, target, type and details). The backend—not the browser—calculates whether each interaction matches a configured decoy target (case-insensitive exact match), then calls the same deterministic verdict engine. The `POST /api/custom-test` endpoint exposes the same capability for API clients. The API accepts at most 100 interactions per case.

This avoids adding a new hardcoded branch for every examiner scenario. It is a **structured test builder**, not an AI/NLP interpreter: a free-text description is saved as context, but verdicts are based on the structured interactions and decoy registry. The test remains simulated input; it does not prove that real MCP traffic was observed.

## Important research limitation
The demo harness generates controlled events internally. The new HTTP and stdio gateway adapters observe supported protocol operations and inject synthetic decoys at the configured gateway boundary. The stdio adapter must run alongside a trusted local server; the HTTP adapter uses a dashboard-saved or environment-configured upstream. Actual sandbox isolation, broader protocol edge-case testing, independent evaluation, and enterprise identity/database integration remain necessary for a stronger production claim. See `docs/06-limitations-and-real-integration.md`.

## Live MCP monitoring gateway (HTTP + stdio)

The project now includes transport adapters for actual MCP protocol messages:

- **Streamable HTTP:** configure approved upstreams with `CANARYTRAP_HTTP_UPSTREAMS`; connect an MCP client to `/gateway/<connection-id>`.
- **stdio:** wrap a trusted local MCP server with the `canarytrap-stdio-proxy` command.
- The gateway injects configured synthetic decoys into supported list responses, intercepts decoy tool/resource/prompt access, records events, and evaluates deterministic verdicts.
- Use the dashboard's **Live MCP Gateway** page to save and activate non-secret HTTP connection settings, test the MCP initialize handshake, generate configuration snippets, and create local stdio wrapper commands. Secret values are not sent through that form.

See [`docs/13-live-gateway.md`](docs/13-live-gateway.md) for setup, example environment variables, security boundaries, and known limitations.

**Scope warning:** this is a research prototype with real transport adapters, not a certified universal MCP firewall. Validate each target server/client combination, deployment security, network controls, storage, and protocol edge cases before using it in a company environment.



## Security Center configuration

Review `.env.example` and `docs/14-security-center.md` before deployment. Configure `CANARYTRAP_RBAC_KEYS` with high-entropy keys and tenant/role assignments, and use HTTPS for remote upstreams and alert webhooks. Private/local upstreams are blocked by default; only set `CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS=true` for explicitly approved internal MCP servers with network egress controls. The dashboard's **Security Center** page exposes the core deterministic controls and reports.

**Scope warning:** inventory and shadow-connection checks can only see configured connections and activity passing through this gateway. The product does not discover every MCP server on a machine/network, and its compliance report is not a certification. Hash-chained SQLite audit data is tamper-evident, not immutable. Webhook delivery is best-effort and payloads are not signed.
