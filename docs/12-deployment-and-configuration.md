# Deployment Wizard and Production Configuration

## What changed

- The dashboard now includes **Setup & Deploy**. Its form runs in the browser and generates a local `.env.production` file plus a deployment checklist. Form values are not submitted to the CanaryTrap backend.
- `render.yaml` provides a Render Blueprint path. After the project is pushed to GitHub, the dashboard can construct the Render Blueprint URL when given the repository URL.
- Docker Compose uses production mode, binds the application correctly inside the container, adds a health check, and persists SQLite data in a named volume.
- In `APP_ENV=production`, the first visit presents an administrator setup form when credentials are not configured. The app stores a salted scrypt password hash and issues an HTTP-only, SameSite session cookie. Later visits use a sign-in form. Environment-configured credentials and HTTP Basic clients remain supported. `/health` and `/ready` remain public health endpoints.
- `/ready` reports configuration readiness but does not certify the application as secure or confirm upstream reachability.
- The Live MCP Gateway page generates configuration for the Streamable HTTP adapter and wrapper commands for the local stdio adapter. See `docs/13-live-gateway.md`.

## Render deployment

1. Push this repository to GitHub. Make sure `render.yaml` is committed.
2. In the Setup & Deploy dashboard page, select Render, enter the repository URL, fill in a strong unique password, and generate the plan. The form does not send values to the app server.
3. Open the Render Blueprint URL and authorize Render to access the repository. Review the plan and persistent disk charges before creating the service.
4. Before exposing the service publicly, preferably set both `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` as Render secret environment variables. If you leave both unset, the first visitor can create the one-time administrator account, so open the deployed URL immediately and complete setup only in a controlled deployment window.
5. Verify `/health` and `/ready`. The setup wizard generates a local environment file only; it does not send credentials to Render. Never commit that file.

The included Render service uses a persistent disk for SQLite. Persistent disks may incur charges and are not a multi-instance database architecture. For multi-instance deployments, replace SQLite with managed PostgreSQL and update the storage layer before scaling.

## Local Docker deployment

1. Copy `.env.example` to `.env`.
2. Leave both `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` commented to use the first-run setup form, or set both to use environment-managed credentials.
3. Run `docker compose up --build -d`.
4. Visit `http://127.0.0.1:8000` and create the administrator, or sign in with the environment-configured credentials.
5. Run `docker compose logs -f canarytrap` to inspect startup logs and `docker compose down` to stop.

## Security notes

- The dashboard session mechanism and optional HTTP Basic guard are minimal access barriers, not replacements for enterprise SSO/OIDC, MFA, or an identity-aware gateway. Use HTTPS for any network-accessible deployment. If you use first-run setup on a public host, anyone reaching the app before you can claim the one-time setup; configure environment credentials first or complete setup in a controlled deployment window.
- Never commit `.env`, downloaded environment files, credentials, or customer data. Rotate any secret that was exposed.
- The HTTP adapter can use a configured upstream bearer token through a server-side environment variable referenced by `token_env`. The dashboard stores only the variable name, never the token value. Add the actual token to the host secret settings before testing the connection.
- The HTTP adapter forwards ordinary traffic to an explicitly configured upstream and injects/intercepts configured synthetic decoys for supported operations. The stdio adapter wraps an approved local process. These are real protocol adapters, but protocol edge cases and target-specific compatibility still need testing.
- Use the current version only for controlled pilots until upstream allowlisting/egress controls, SSO/RBAC, managed database support, alerting, backup/restore, retention controls, sandbox isolation and independent security evaluation are complete.
