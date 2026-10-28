# Security Center — deterministic controls

This module adds non-AI/non-ML controls to MCP-CanaryTrap. It is a prototype and must be tested against each approved MCP client/server before deployment.

## Dashboard
Open **Security Center** from the sidebar. It supports policy creation, server inventory, posture checks, inventory reconciliation, observed unregistered connection checks, cross-server correlation, deterministic policy smoke tests, frequency baselines, audit-chain verification, compliance-style posture output, and webhook configuration.

## Policies
- Actions: `allow`, `deny`, `monitor`.
- Operation: `*`, `tools/call`, `resources/read`, or `prompts/get`.
- Target matching: exact name, `*`, or a trailing wildcard such as `canarytrap://secret/*`.
- The first enabled matching rule in creation order is applied. If no rule matches, the default is `allow`; set `CANARYTRAP_DEFAULT_POLICY_ACTION=deny` to default-deny supported operations (then create explicit allow rules).
- `deny` is enforced by the HTTP and stdio gateway for supported tool-call/resource-read/prompt-get requests. List/initialize protocol messages are not governed by these target policies.
- Policy rules are scoped to the tenant assigned to the gateway API key, or `CANARYTRAP_DEFAULT_TENANT` when API-key RBAC is not configured.

## Inventory and discovery boundaries
Inventory is operator-maintained. `/api/security/inventory/reconcile` compares configured HTTP gateway connections with registered inventory. `/api/security/inventory/shadow` identifies connection IDs observed in the gateway audit trail that are not registered. These are **not** operating-system or network-wide discovery and cannot detect a server whose traffic never reaches CanaryTrap.

## RBAC and tenant isolation
Set `CANARYTRAP_RBAC_KEYS` to a JSON map of API keys to role/tenant, for example:

```json
{
  "replace-with-a-long-random-admin-key": {"role":"admin","tenant":"default","actor":"admin"},
  "replace-with-a-long-random-operator-key": {"role":"operator","tenant":"default","actor":"operator"},
  "replace-with-a-long-random-viewer-key": {"role":"viewer","tenant":"default","actor":"viewer"}
}
```

Use unique, high-entropy keys; store them only in the server environment. Admin can manage policies, inventory, tenants and webhooks; operator can manage policies/inventory and run simulations; viewer can read. If this variable is configured, the HTTP gateway requires `X-CanaryTrap-API-Key` and does not forward that header to the upstream. In local development without the key map, endpoints use a convenience admin context. Production still requires the existing dashboard Basic Auth; configure both layers appropriately. This is not a replacement for an enterprise identity provider or a secret manager. The deployment-level HTTP upstream connection registry remains shared configuration for operators; per-tenant policies, inventory, audit, baselines, simulations, and test sessions are tenant-scoped.

## SSRF / upstream URL safeguards
By default, obvious loopback/private/link-local/reserved IP literals and `.localhost`, `.local`, `.internal` hostnames are blocked. Cloud metadata hostnames are blocked. For intentional private-network MCP servers, set `CANARYTRAP_ALLOW_PRIVATE_UPSTREAMS=true` only after reviewing the risk and restricting network egress. `CANARYTRAP_ALLOWED_UPSTREAM_HOSTS` optionally restricts upstreams to a comma-separated list of exact hostnames. These application checks do not eliminate DNS rebinding or every SSRF path; enforce outbound firewall/egress rules at deployment level.

## Audit and alerts
Gateway interactions create tenant-scoped SHA-256 hash-chained audit entries. `/api/security/audit/verify` verifies the stored chain. This is tamper-evident, not immutable: someone with full database access could rewrite the entire chain. Export audit evidence/hashes to separate append-only storage for stronger guarantees.

Webhook delivery is best-effort and bounded by a two-second HTTP timeout. Only HTTPS URLs are accepted, redirects are disabled, and payloads exclude tool arguments and results. Webhook payloads are not currently signed, and receiver-side authentication/verification must be added before sensitive production use. Failed webhook delivery does not stop MCP traffic.

## Deterministic baselines, correlation, and simulations
Baselines are simple operation/target frequency counts from recorded gateway events, not anomaly-detection ML. Cross-server correlation groups exact operation/target pairs and counts observed connection IDs. The built-in simulation tests policy matching only; it does not attack a live MCP server. The compliance-style report is a self-assessment, not legal certification.

## API index
- `GET /api/security/overview`
- `GET|POST /api/security/policies`; `DELETE /api/security/policies/{rule_id}`
- `GET|POST /api/security/inventory`; `DELETE /api/security/inventory/{server_id}`
- `POST /api/security/inventory/reconcile`
- `GET /api/security/inventory/shadow`
- `POST /api/security/posture/scan`
- `POST /api/security/simulate`; `GET /api/security/simulations`
- `GET /api/security/baselines`; `POST /api/security/baselines/rebuild`
- `GET /api/security/correlation`
- `GET /api/security/audit`; `GET /api/security/audit/verify`
- `GET /api/security/reports/compliance`
- `GET|POST /api/security/tenants`
- `POST /api/security/webhook`

Run the full regression suite with `python -m pytest -v`.
