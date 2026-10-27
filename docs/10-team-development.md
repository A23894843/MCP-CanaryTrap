# 10 — Team Development Guide

## Before starting Phase 2

From the repository root:

```bash
python -m pytest -v
python -m mcp_canarytrap.client
```

## Branching

Use a dedicated Phase 2 branch, for example:

```bash
git checkout -b phase2-sandbox
```

## Layering rule

Keep these responsibilities separate:

```text
MCP protocol
    ↓
decoy design
    ↓
sandbox
    ↓
interaction logging
    ↓
verdict
    ↓
reporting
```

## Documentation rule

For each new security mechanism, document:

1. what it solves;
2. why it is needed;
3. assumptions;
4. evidence produced;
5. limitations.

## Safety rule

Use fabricated data only. Never put real passwords, API keys, credentials or confidential records into a decoy. Do not implement destructive administrative actions merely to make a decoy look realistic.
