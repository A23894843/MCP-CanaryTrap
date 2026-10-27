# MCP-CanaryTrap — Project Overview

## Problem
MCP servers expose tools, resources and prompts to AI applications. A static capability list describes what is available, but does not by itself show which exposed resources a server or test agent actually attempts to access during a task.

## Proposed idea
CanaryTrap adds fictional decoys to a controlled test environment. A deterministic policy flags a session when an observed interaction targets a decoy. The verdict includes event IDs that provide evidence for the result.

## Project stages
1. **MCP foundation and decoy design:** sample MCP server/client, three-category taxonomy, session-derived placement.
2. **Harness and logging:** controlled benign and overreaching scenarios, interaction event model, SQLite storage.
3. **Deterministic verdict:** `CLEAN` when no recorded event touches a decoy; `FLAGGED` when one or more do.
4. **Reporting:** FastAPI endpoints and local browser dashboard.
5. **Evaluation:** regression tests for benign/overreaching paths, evidence checks, limitations and future integration plan.

## What is complete in this source package
This is a complete **demonstration prototype** for a professor presentation. It includes a runnable end-to-end simulation, persistent audit records, deterministic verdicts, API/dashboard, tests, Docker files and project documentation.

## Important scope limitation
The harness currently simulates interaction events; it does **not** transparently monitor or intercept arbitrary third-party MCP servers. A research-grade live integration requires a server adapter/proxy that observes actual MCP requests and responses, plus sandbox isolation. Do not claim this prototype has validated evasion resistance or production security.
