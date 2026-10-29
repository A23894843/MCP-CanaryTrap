# MCP-CanaryTrap v1.3.1 — Authentication Fix Verification

## Fixes

- Added a first-run administrator setup form when production credentials are absent.
- Added a browser sign-in form and server-side session cookies (`HttpOnly`, `SameSite=Strict`, 12-hour expiry).
- Stores a salted `scrypt` password hash in the persistent SQLite database; plaintext passwords are not persisted.
- Makes first-run setup one-time and returns clear validation/conflict errors instead of leaving the dashboard in an unusable 503 state.
- Preserves environment-configured `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` and HTTP Basic authentication for API clients.
- Updates Docker Compose, Render Blueprint, deployment documentation, readiness checks, and Security Center posture checks for the new flow.

## Verification

Command: `python -m pytest -q`

Result: **42 passed, 1 skipped**. The skipped test is an existing optional integration test.

Command: `python -m compileall -q src tests`

Result: passed.

## Important deployment note

First-run setup is one-time but is not a substitute for a controlled deployment process. On a public host, configure environment credentials before exposing the service, or complete first-run setup immediately in a controlled window; otherwise, a visitor who reaches the service first could claim the initial administrator account. Use HTTPS for network-accessible deployments and ensure the SQLite database is persistent and writable.
