# Architecture

```text
Python MCP Client
       | MCP over STDIO
       v
Instrumented MCP Server (normal + decoy tools)
       |
  monitor_tool()
       v
Rule-based detector -- exact name match --> severity policy
       |
       v
SQLite event store
       ^
       |
FastAPI monitoring API --> Browser dashboard

Dashboard manual inspection --> HTTP API --> detector --> SQLite
```

The MCP client route and dashboard manual-inspection route are distinct. Both reuse the same detection and storage modules.
