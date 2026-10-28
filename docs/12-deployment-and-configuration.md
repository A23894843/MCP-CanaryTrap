# Deployment Wizard and Production Configuration

## What changed

- The dashboard now includes **Setup & Deploy**. Its form runs in the browser and generates a local `.env.production` file plus a deployment checklist. Form values are not submitted to the CanaryTrap backend.
- `render.yaml` provides a Render Blueprint path. After the project is pushed to GitHub, the dashboard can construct the Render Blueprint URL when given the repository URL.
- Docker Compose now requires dashboard credentials, uses production mode, binds the application correctly inside the container, adds a health check, and persists SQLite data in a named volume.
- In `APP_ENV=production`, the dashboard and API routes require HTTP Basic authentication. `/health` and `/ready` remain public health endpoints. Baseline security headers are added.
- `/ready` reports configuration readiness but does not certify the application as secure or confirm upstream reachability.
- The Live MCP Gateway page generates configuration for the Streamable HTTP adapter and wrapper commands for the local stdio adapter. See `docs/13-live-gateway.md`.

## Render deployment

1. Push this repository to GitHub. Make sure `render.yaml` is committed.
2. In the Setup & Deploy dashboard page, select Render, enter the repository URL, fill in a strong unique password, and generate the plan. The form does not send values to the app server.
3. Download the generated `.env.production` locally. In Render's environment settings, add `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD` using the values you chose in the wizard. Render does not receive these values from the dashboard automatically; never commit the downloaded file.
4. Open the Render Blueprint URL and authorize Render to access the repository. Review the plan and persistent disk charges before creating the service.
5. After deployment, use the dashboard username and generated password configured in Render. Verify `/health` and `/ready`.

The included Render service uses a persistent disk for SQLite. Persistent disks may incur charges and are not a multi-instance database architecture. For multi-instance deployments, replace SQLite with managed PostgreSQL and update the storage layer before scaling.

## Local Docker deployment

1. Copy `.env.example` to `.env`.
2. Replace `DASHBOARD_PASSWORD` with a unique password of at least 16 characters. Set `DASHBOARD_USERNAME` as needed.
3. Run `docker compose up --build -d`.
4. Visit `http://127.0.0.1:8000`; the browser will request Basic Authentication credentials.
5. Run `docker compose logs -f canarytrap` to inspect startup logs and `docker compose down` to stop.

## Security notes

- The HTTP Basic guard is a minimal access barrier, not a replacement for enterprise SSO/OIDC, role-based access control, MFA, or an identity-aware gateway. Use HTTPS for any network-accessible deployment.
- Never commit `.env`, downloaded environment files, credentials, or customer data. Rotate any secret that was exposed.
- The HTTP adapter can use a configured upstream bearer token through a server-side environment variable referenced by `token_env`. The dashboard stores only the variable name, never the token value. Add the actual token to the host secret settings before testing the connection.
- The HTTP adapter forwards ordinary traffic to an explicitly configured upstream and injects/intercepts configured synthetic decoys for supported operations. The stdio adapter wraps an approved local process. These are real protocol adapters, but protocol edge cases and target-specific compatibility still need testing.
- Use the current version only for controlled pilots until upstream allowlisting/egress controls, SSO/RBAC, managed database support, alerting, backup/restore, retention controls, sandbox isolation and independent security evaluation are complete.
