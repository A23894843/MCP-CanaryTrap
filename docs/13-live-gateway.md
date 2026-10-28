# Live MCP gateway adapters (HTTP + stdio)

This increment adds **real protocol-message interception** for two supported integration paths. It is still a security research prototype, not a certified production security product.

## 1. Streamable HTTP MCP upstream

Configure upstream servers in the server environment. Do not submit bearer tokens through the browser form.

```bash
export CANARYTRAP_HTTP_UPSTREAMS='{
  "internal-docs": {
    "url": "https://mcp.example.com/mcp",
    "token_env": "INTERNAL_DOCS_MCP_TOKEN",
    "decoy_tools": ["canarytrap_decoy_admin", "canarytrap_decoy_export"],
    "decoy_resources": ["canarytrap://secret/payroll"],
    "decoy_prompts": ["canarytrap_decoy_policy"]
  }
}'
export INTERNAL_DOCS_MCP_TOKEN='set-this-in-your-secret-manager'
```

Use `https://<canarytrap-host>/gateway/internal-docs` as the MCP endpoint in a compatible client. The configured upstream URL must be the upstream MCP endpoint, not just its website home page. The `token_env` field is optional; when supplied, the gateway adds `Authorization: Bearer <secret>` to upstream requests and requires HTTPS for that upstream in production. The HTTP request body is capped by `CANARYTRAP_MAX_REQUEST_BYTES` (default 2 MiB). The dashboard's Live MCP Gateway page can save and activate the non-secret connection configuration in the persistent SQLite store, or generate the same JSON locally for environment-based configuration. It never stores bearer-token values.

The HTTP adapter forwards ordinary requests and responses. It adds configured synthetic decoys to successful `tools/list`, `resources/list`, and `prompts/list` JSON-RPC responses. Calls to configured decoy tools, resources, and prompts are intercepted at the gateway and answered synthetically, so the request is not sent upstream. Access attempts are persisted in the existing SQLite event store and evaluated by the deterministic verdict engine. The adapter supports JSON responses and transforms JSON-RPC messages inside streamed SSE data frames. JSON-RPC batch requests are not yet supported by the monitoring layer; validate protocol edge cases with the target MCP implementation.

## 2. Local stdio MCP server

The stdio adapter is a wrapper process, not a hosted remote process runner. The wrapper and downstream server must run on the same host/container. Example:

```bash
canarytrap-stdio-proxy \
  --connection-id internal-files \
  --decoy-tool canarytrap_decoy_admin \
  --decoy-resource canarytrap://secret/payroll \
  --decoy-prompt canarytrap_decoy_policy \
  -- python /opt/approved-mcp-server/server.py
```

Configure the MCP client to launch the command above instead of launching the downstream server directly. MCP protocol messages remain on stdout; the child server's stderr is inherited. The wrapper records observed tool calls, resource reads, and prompt gets without persisting tool arguments or results. The configured decoy calls are answered locally and are not forwarded to the downstream server.

Only wrap a server command you trust. The stdio wrapper launches a local child process with the current user's privileges; never expose a public endpoint that accepts arbitrary shell commands.

## 3. Dashboard and status

- `POST /api/gateway/connections` saves non-secret configuration immediately; `DELETE /api/gateway/connections/{id}` removes a dashboard-saved entry. `POST /api/gateway/connections/{id}/test` sends an MCP initialize handshake to test upstream reachability. `GET /api/gateway/config` returns connection IDs, URLs, decoy counts, and whether the referenced token environment variable exists. These endpoints never return secret values.
- `GET /ready` reports basic process/configuration status only; it does not prove the upstream server is reachable.
- `GET /health` is a liveness check.
- Events and verdicts appear in the existing Events & Evidence and Test Sessions pages.

## 4. Important limitations before production use

- The gateway must be tested against each target MCP client/server SDK and protocol version. It is not a universal transparent proxy certification.
- HTTP upstreams can be configured through the dashboard and become active immediately in the SQLite-backed configuration, or loaded from the server-side CANARYTRAP_HTTP_UPSTREAMS environment variable. A referenced bearer-token environment variable must already exist in the hosting environment before the upstream can be used.
- The stdio adapter is intended for a trusted local process and does not offer remote command execution from the dashboard.
- Use HTTPS externally, a secret manager, least-privilege service accounts, an upstream URL allowlist/network egress policy, centralized logs, backups, retention limits, rate limits, and organization SSO/RBAC before company deployment.
- SQLite is appropriate for a single-instance prototype. Use a managed PostgreSQL backend and migrations for multi-instance/high-availability deployments.
- A decoy interaction is evidence of access to a synthetic decoy, not proof of malicious intent. Decoy names must be unique and must not collide with legitimate upstream resources.
- The gateway currently focuses on tools/resources/prompts list and access operations. Validate sampling, roots, elicitation, notifications, cancellation, reconnect/session expiry, batch requests, long-lived SSE streams, unusual headers, and server-specific extensions before relying on it in production.
- Do not connect to an MCP server you do not own or have permission to test. Do not put real sensitive data in decoy assets.
