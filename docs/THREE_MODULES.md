# MCP-CanaryTrap — Three-Module Assessment Design

The existing project title remains **MCP-CanaryTrap**.

## Module 1 — Vulnerable Environment & Attack-Flow Simulation
`python -m app.security.lab_simulator`

The simulator models the trust-boundary problem using a supplied endpoint string and creates a harmless marker file. It does not invoke a shell, browser, or vulnerable third-party package. This provides a safe classroom demonstration of the data-flow and impact concept without executing arbitrary commands.

## Module 2 — Local Config & Dependency Auditor
`python -m app.security.security_cli .`
`python -m app.security.security_cli --json ~/path/to/project`

Scans selected paths for package manifests, lockfiles, and MCP client JSON configuration references. It flags affected version declarations/resolutions and configuration references that need manual version resolution. Npx caches can be supplied as scan paths, but cache formats vary; absence of a finding is not proof that no vulnerable copy exists.

## Module 3 — Runtime URL Sanitizer / Security Proxy
Run the FastAPI app and use:
`POST /api/security/validate-authorization-endpoint`

Example JSON body:
`{"authorization_endpoint":"https://login.example.org/oauth/authorize"}`

The validator is a strict policy gate. It permits HTTPS URLs with a hostname and rejects non-HTTPS schemes, embedded credentials, control characters, malformed ports, and shell-control characters. This is a local validation boundary, not a drop-in patch for mcp-remote and not a complete OAuth security implementation.
