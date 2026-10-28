# Live MCP Integration: Scope and Remaining Work

## Current implementation status
The package contains both a controlled simulation harness and transport-aware monitoring adapters for configured MCP connections:

- **Streamable HTTP:** an authenticated FastAPI reverse-proxy route forwards ordinary requests to an environment-configured upstream, injects synthetic decoys into supported list responses, intercepts configured decoy access, and records evidence.
- **stdio:** a local wrapper process launches a trusted downstream MCP server, observes JSON-RPC messages, injects synthetic decoy definitions into supported list responses, and answers decoy access locally.
- **Dashboard:** generates configuration snippets and wrapper commands locally; secrets are referenced by environment-variable name and are not posted by the form.

This is a research prototype. It is not a universal MCP firewall and has not been independently security-certified. The gateway must be tested with each intended MCP client/server SDK and protocol version.

## Remaining engineering work
1. Add managed PostgreSQL storage and schema migrations for multi-instance deployments.
2. Replace HTTP Basic authentication with organization SSO/OIDC and role-based access control.
3. Add a strict upstream hostname allowlist, egress policy, rate limits, request-size limits and operational alerting.
4. Test cancellation, reconnect/session expiry, notifications, protocol-version negotiation, sampling, roots, elicitation, malformed messages, batch messages and long-lived SSE behaviour against real implementations.
5. Add actual sandbox isolation for downstream processes, with restricted mounts, filesystem access, credentials and network egress.
6. Run a broad benign/overreaching evaluation corpus and report true positives, false positives, false negatives, throughput, latency and failure modes.
7. Add backup/restore, retention controls, secret rotation, incident response, security review and deployment rollback procedures.

## Research experiments still required
- Compare naming and description similarity between genuine and decoy items.
- Measure whether session-specific placement reduces simple fingerprinting.
- Evaluate multiple benign tasks and multiple overreaching behaviors.
- Report true positives, false positives, false negatives and limitations.
- Test reproducibility across Python/SDK versions.

## Claim boundary for presentations
Say: “This prototype provides configured HTTP and local stdio MCP monitoring adapters that inject synthetic decoys and record deterministic access verdicts for supported protocol operations.”
Do not say: “It detects all malicious MCP servers,” “evasion resistance is proven,” or “it is production-certified.”
