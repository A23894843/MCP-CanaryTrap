# Architecture

```text
MCP stdio client
      |
      v
MCP-CanaryTrap MCP server
      |
      +--> deterministic decoy detector
      |       +--> CLEAN / FLAGGED verdict
      |
      +--> SQLite security event log
      |
      +--> Canary Evidence Ledger (SHA-256 linked records)

Browser / examiner
      |
      v
FastAPI multi-page web application
      +--> Dashboard
      +--> Decoy Lab --> /inspect --> detector
      +--> CVE Prototype --> /api/cve/guard-check --> auth + Host + Origin checks
      +--> Evidence Ledger --> /api/evidence/verify
```

The CVE guard endpoint is a control demonstration, not a transparent reverse proxy. To protect a real upstream MCP service, the guard must sit on the only network path to that service, reject unauthenticated requests before dispatch, and the upstream port must not be externally reachable.
