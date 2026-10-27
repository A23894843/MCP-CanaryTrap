# 08 — Phase 1 Architecture

## MCP foundation

```text
                    Host concept
                         │
                         ▼
                    MCP Client
                         │
                    MCP / stdio
                         │
                         ▼
                    MCP Server
                  /      |       \
                 ▼       ▼        ▼
              Tools  Resources  Prompts
```

## Phase 1 runtime demonstration

```text
Client
  │
  ├── establish session
  ├── inspect capabilities
  ├── list tools
  ├── list resources
  ├── list resource templates
  ├── list prompts
  ├── call tool
  ├── read resource
  └── get prompt
```

## CanaryTrap design side

```text
session_id
    │
    ▼
deterministic_seed()
    │
    ▼
create_placement_plan()
    │
    ▼
PlacementPlan
    │
    └── ordered Decoy objects
```

## Handoff boundary

```text
PHASE 1
MCP foundation + decoy taxonomy + placement scaffold
                    │
                    ▼
PHASE 2
sandbox harness + decoy generation + interaction logging
                    │
                    ▼
PHASE 3 / later
deterministic verdict + evidence + evaluation
```

The Phase 1 server is safe and self-contained. It does not monitor external servers, access real secrets, or perform destructive operations.
