# MCP-CanaryTrap v1.3.0 — Verification Report

Date: 2026-10-28

## Automated checks
- `python -m pytest -q -rs`: **38 passed, 1 skipped**.
- Skipped: `tests/test_mcp_server.py` because the `mcp` SDK was not installed in the verification runtime (`No module named 'mcp'`). The dependency is declared in `pyproject.toml`; rerun tests after installing `python -m pip install -e ".[dev]"`.
- Python source compilation: passed.
- Dashboard JavaScript syntax (`node --check`): passed.
- Dashboard smoke test: `/` returned HTTP 200 and rendered the Security Center.
- OpenAPI generation: passed; 18 Security Center route paths were present at verification.
- `docker-compose.yml` and `render.yaml` parsed as YAML.
- HTML duplicate-ID check: no duplicate IDs found.

## Implemented in this release
- Deterministic `allow` / `deny` / `monitor` policy rules with HTTP and stdio enforcement for `tools/call`, `resources/read`, and `prompts/get`.
- Tenant-scoped security data, API-key role checks, and tenant-scoped simulation sessions/events.
- Operator-managed MCP inventory and reconciliation against configured HTTP gateway connections.
- Detection of unregistered connection IDs observed in CanaryTrap gateway audit records.
- Posture checks, deterministic policy smoke test, deterministic frequency baselines, and exact-match cross-server correlation.
- SHA-256 hash-chained gateway audit entries and a verification endpoint.
- HTTPS webhook configuration and best-effort minimal-metadata notifications on decoy detections / denied policy actions.
- Compliance-style posture report.
- Basic SSRF hardening for obvious private/loopback/link-local/reserved IP literals, internal hostnames, metadata hostnames, and URL query/fragment credentials; optional exact-host allowlist.
- Dashboard Security Center and deployment environment documentation.

## Important limitations
- No AI or ML code was added.
- Inventory is operator-maintained. Reconciliation and shadow checks do not discover arbitrary servers on a host or network; only configured/observed gateway connections are visible.
- HTTP upstream connection configuration is deployment-shared. Security policies, inventory, audit, baselines, simulations, and test sessions are tenant-scoped.
- SSRF checks do not eliminate DNS rebinding or every network path; enforce egress restrictions at the deployment layer.
- Webhook delivery is best-effort and payloads are not signed. Add receiver authentication/signature verification before sensitive production use.
- Hash chaining detects stored edits but is not immutable if an attacker controls the database; export evidence to independent append-only storage.
- The compliance-style report is not legal certification, and this prototype has not undergone independent security review.
