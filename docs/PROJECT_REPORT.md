# MCP-CanaryTrap — Project Report (Repository Documentation)

## Project title
**MCP-CanaryTrap: A Deterministic Decoy-Injection Mechanism for Detecting Overreaching Behavior in Model Context Protocol (MCP) Servers**

## Abstract
AI applications increasingly use the Model Context Protocol (MCP) to connect with external tools and services. Static inspection of manifests and permissions describes declared capabilities, but does not by itself establish what a running server attempts to access. MCP-CanaryTrap proposes a deterministic runtime signal: introduce fabricated tools, credentials and data assets with no legitimate role in a controlled test task, then record any interaction with those decoys. The current repository implements a proof of concept with 30 fictional decoy tool names, exact-name matching, SQLite event logging and a FastAPI dashboard. It also includes supporting educational utilities related to CVE-2025-6514. Generalized placement into arbitrary third-party sessions, fingerprinting resistance and formal multi-server evaluation remain research objectives rather than completed capabilities.

## Problem statement
Existing configuration-level MCP review cannot, by itself, determine whether a running server attempts to access resources beyond those needed for its assigned task. The project investigates whether decoy interactions can provide an explainable, deterministic runtime observation without relying on learned anomaly scores or probability thresholds.

## Objectives from the official synopsis
1. Design a taxonomy for fabricated MCP tools, credentials and data assets.
2. Design a placement strategy that preserves legitimate task behavior and resists decoy fingerprinting.
3. Implement deterministic detection and a binary verdict for configured decoy interactions.
4. Study evasion resistance and harden the decoy taxonomy.
5. Evaluate legitimate and deliberately misbehaving test servers.

## Implemented prototype
- **Decoy taxonomy:** 30 fictional MCP tool names are configured in the instrumented server.
- **Deterministic detection:** exact-name matching against the configured decoy catalogue.
- **Verdict and event:** a matching tool call creates a structured `DECOY_ACCESS` event with configured severity and timestamp.
- **Persistence:** SQLite stores event history.
- **Dashboard/API:** FastAPI provides the integrated monitoring interface and assessment endpoints.
- **Supporting CVE modules:** safe vulnerable-flow simulation, local dependency/configuration auditing, and authorization-endpoint URL policy validation.

## Proposed research work not yet implemented or validated
- General decoy injection into arbitrary external MCP server sessions.
- A placement algorithm/strategy that is empirically shown not to affect legitimate tasks.
- Evidence that decoys are statistically indistinguishable from genuine assets.
- Evasion-resistant construction validated against fingerprinting attempts.
- A controlled evaluation corpus of independent legitimate and deliberately misbehaving servers.
- Measured detection rate and false-positive rate. Do not claim zero false positives without completing and documenting this evaluation.

## System methodology
1. Configure fictional decoy tool names in the instrumented MCP server.
2. Receive a tool invocation through the instrumented server.
3. Compare the invoked tool name against the configured decoy catalogue.
4. If matched, create and persist a structured event in SQLite.
5. Display the event in the dashboard for human review.

This method observes only interactions routed through the instrumented server or explicit application inspection endpoints. It is not a network-wide monitor and does not automatically inspect arbitrary third-party MCP servers.

## CVE-2025-6514 supporting case study
CVE-2025-6514 describes OS command injection in `mcp-remote` when connecting to untrusted MCP servers due to crafted input in the OAuth `authorization_endpoint` response URL. The reported affected versions are 0.0.5 through 0.1.15; version 0.1.16 is fixed. The weakness is CWE-78. The project includes safe simulation and defensive assessment helpers; it does not patch the upstream package and does not execute a live exploit.

### Official and technical references
- NVD: https://nvd.nist.gov/vuln/detail/CVE-2025-6514
- GitHub Security Advisory: https://github.com/advisories/GHSA-6xpm-ggf7-wc3p
- JFrog technical analysis: https://research.jfrog.com/vulnerabilities/mcp-remote-command-injection-rce-jfsa-2025-001290844/

## Manual verification
Use the Python MCP client to invoke a configured decoy and verify that an event appears. Invoke the normal `weather_search` tool and verify that it does not produce a decoy event. Also manually exercise the auditor, URL validator and safe simulator. Record actual outcomes and screenshots; do not report unperformed tests as successful.

## Limitations
- Exact-name detection can only see calls routed through the instrumented server.
- A decoy hit is a signal for investigation, not conclusive proof of malicious intent in every context.
- General placement, decoy indistinguishability and fingerprinting resistance are not yet demonstrated.
- The current prototype has no formal multi-server benchmark or measured false-positive rate.
- CVE utilities are educational checks, not a substitute for upgrading vulnerable software.

## Conclusion
The repository demonstrates the core deterministic decoy matching and event-logging path in an instrumented MCP environment. It provides a foundation for the broader research proposal. The next major work is a controlled decoy placement and evaluation harness capable of testing independent MCP servers and measuring evasion and false-positive behavior.
