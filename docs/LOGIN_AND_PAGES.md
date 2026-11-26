# Login system and page layout

- First start redirects to `/setup`; create a password at least 12 characters long.
- Password configuration is saved in `data/auth.json` as a random-salt PBKDF2-HMAC-SHA256 hash (310,000 iterations), not plaintext.
- Later visits redirect to `/login`; the existing password is verified. Password setup is not repeated at each login.
- Session cookie is signed, HttpOnly (Starlette SessionMiddleware default), SameSite=Strict, and expires after eight hours.
- Logout clears the session.
- The session signing secret is persisted in `data/.session_secret`; do not commit either `data/auth.json` or `data/.session_secret`.
- All dashboard and `/api/*` routes require a session. `/health`, `/docs`, `/redoc`, `/openapi.json`, auth routes and static assets are public.
- This is a local educational prototype. Before network exposure, configure HTTPS, secure cookies, CSRF protection for all state-changing endpoints, rate limiting, account recovery and production secret management.

## Separate pages
`dashboard.html`, `cve.html`, `simulation.html`, `auditor.html`, `url-validator.html`, `decoy-monitor.html` are separate pages. Their JavaScript is split into `common.js`, `dashboard.js`, `simulation.js`, `auditor.js`, `url-validator.js`, and `decoy-monitor.js`.


## Render deployment note
SessionMiddleware is deliberately registered after the login-protection middleware so it is the outer ASGI middleware and populates `request.session` before authentication checks run. The Render deployment launcher binds to `0.0.0.0` and uses the platform-provided `PORT`. Secure session cookies are enabled for HTTPS deployments.
