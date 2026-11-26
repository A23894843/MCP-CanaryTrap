# MCP-CanaryTrap

**A deterministic decoy-injection and evidence platform with a CVE-2026-5029 request-boundary mitigation prototype.**

MCP-CanaryTrap is an educational defensive security project. It exposes fictional MCP decoys, deterministically flags interaction with them, records security events, and provides a safe demonstration of authentication and request metadata checks relevant to the attack path described by CVE-2026-5029.

## What is included

### Phase 1 — Deterministic decoy detection
- Fictional decoys: `admin_config`, `customer_backup`, `system_secrets`.
- Exact, case-insensitive matching.
- Clear `FLAGGED` or `CLEAN` verdicts with a trigger explanation.
- MCP server tools and a simple MCP stdio client.
- FastAPI inspection endpoint and event history.

### Phase 2 — CVE-2026-5029 gateway-control prototype
- Bearer token authentication.
- Host allowlist.
- Optional Origin allowlist validation.
- Fail-closed behavior if critical configuration is missing.
- Blocked and accepted decisions are recorded.
- Examiner page with NVD, CERT Polska, GitHub Advisory and upstream links.

**Important boundary:** the `/api/cve/guard-check` route demonstrates the control logic in this application. It is not a drop-in patch for the upstream Code Runner MCP server and does not automatically intercept another service's `/mcp` endpoint. For real deployment, put the vulnerable upstream on a private network and route all external MCP traffic through a gateway that invokes equivalent checks before proxying requests. Never expose the upstream port directly.

### Unique feature — Canary Evidence Ledger
Each decoy event and CVE gateway decision creates a canonical JSON record linked to the previous record using SHA-256. `/api/evidence/verify` recomputes the chain and reports whether the stored evidence has changed. This gives an examiner a concrete way to verify audit integrity. It is tamper-evident, not tamper-proof; a production system should anchor hashes in an external immutable store and serialize concurrent writes.

## Project layout

```text
MCP-CanaryTrap/
├── app/
│   ├── api/routes.py
│   ├── core/
│   │   ├── cve_guard.py
│   │   ├── decoys.py
│   │   ├── detector.py
│   │   └── evidence.py
│   ├── storage/database.py
│   ├── main.py
│   ├── mcp_client.py
│   └── mcp_server.py
├── data/                  # SQLite DB is created on first run
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CVE-2026-5029.md
│   └── DEMO-GUIDE.md
├── scripts/
│   └── verify_project.py
├── static/css/style.css
├── static/js/
├── templates/
├── .env.example
├── Dockerfile
├── render.yaml
└── requirements.txt
```

## Run locally

Python 3.11+ recommended.

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env and set a long random token.
uvicorn app.main:app --reload
```

Open:
- Home: http://127.0.0.1:8000/
- Dashboard: http://127.0.0.1:8000/dashboard
- Decoy Lab: http://127.0.0.1:8000/decoy-lab
- CVE Prototype: http://127.0.0.1:8000/cve-protection
- Evidence Ledger: http://127.0.0.1:8000/evidence
- API docs: http://127.0.0.1:8000/docs

## CVE demo configuration

Set `.env` (or your deployment environment):

```env
CANARYTRAP_CVE_TOKEN=replace-with-a-long-random-secret
CANARYTRAP_ALLOWED_HOSTS=127.0.0.1,localhost
CANARYTRAP_ALLOWED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
```

Restart the server after changing environment variables. In the CVE page, use the configured token, `localhost:8000` as Host and `http://localhost:8000` as Origin.

Expected outcomes:
- Missing token → HTTP 401.
- Wrong token → HTTP 403.
- Host not allowlisted → HTTP 400.
- Origin not allowlisted → HTTP 403.
- Valid token and allowed Host/Origin → HTTP 200.

Do not put a real production secret in screenshots, source control or the examiner demo recording.

## Manual verification

```bash
python scripts/verify_project.py
```

The script checks deterministic decoy decisions, the CVE guard outcomes and the evidence-chain integrity using a temporary database. It does not attack or execute code on a vulnerable server.

## MCP stdio demonstration

```bash
python app/mcp_client.py
```

The client starts `app/mcp_server.py` as a child process, initializes an MCP session, lists tools and lets you call a tool. Try `weather_search` (normal) and `system_secrets` (decoy). The decoy call is flagged and written to SQLite.

## Deployment notes

- Render configuration is included as a starting point.
- SQLite on ephemeral hosting may be reset on redeploy/restart. Use a persistent disk or managed PostgreSQL for durable deployment.
- Configure a strong secret in Render environment variables; never commit `.env`.
- For multi-worker production, replace the SQLite hash-chain writer with a transactional database/append-only event service and serialize chain writes.
- Bind upstream MCP services to a private interface/network. Do not expose the vulnerable upstream service directly.

## CVE references

- [NVD — CVE-2026-5029](https://nvd.nist.gov/vuln/detail/CVE-2026-5029)
- [CERT Polska advisory](https://cert.pl/en/posts/2026/05/CVE-2026-5029/)
- [GitHub Security Advisory GHSA-jv4w-6p47-rhcx](https://github.com/advisories/GHSA-jv4w-6p47-rhcx)
- [Affected upstream project](https://github.com/formulahendry/mcp-server-code-runner)

## Authorship and presentation

Present this as your implementation and explain the design decisions you understand and can defend. The distinct project contribution to highlight is the **Canary Evidence Ledger**, alongside deterministic decoy detection and the CVE request-boundary demonstration. Credit the public CVE advisory sources and any third-party libraries. Do not claim the vulnerability is fully fixed by this prototype.

## GitHub commit checklist

Before pushing:
1. Review `.env.example` and keep your real `.env` file untracked.
2. Confirm `data/canarytrap.db` is not committed; the database is created at runtime.
3. Run `python scripts/verify_project.py`.
4. Run `python -m compileall app scripts`.
5. Commit the source, documentation, templates, static assets, and deployment files.

Suggested first commit:

```bash
git init
git add .
git commit -m "Initial release: MCP-CanaryTrap integrated prototype"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repository>.git
git push -u origin main
```

Replace the remote URL with your actual GitHub repository URL.
