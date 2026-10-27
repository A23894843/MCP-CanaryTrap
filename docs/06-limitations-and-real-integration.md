# Limitations and Roadmap to Live MCP Integration

## Honest current status
The package has an end-to-end local simulation, persistent logs, a deterministic verdict, a web dashboard and tests. The MCP SDK server/client examples demonstrate protocol primitives separately. The harness does not yet observe live traffic from an arbitrary MCP server.

## What a live adapter needs
1. Define supported transport(s), initially local stdio and/or Streamable HTTP.
2. Place a controlled client/proxy/adapter at the boundary where tool calls and resource reads are visible.
3. Record actual MCP request method, target, arguments metadata (redacted), response status and correlation/session ID.
4. Map actual target names/URIs to the session's decoy inventory.
5. Ensure the logger does not record secrets or unnecessary personal data.
6. Test timeout, cancellation, malformed messages, server restart and transport failure.
7. Run the server under test in an actual isolation boundary such as a dedicated container with restricted mounts/network.
8. Compare observations against an independently reviewed benign/overreaching test corpus.

## Research experiments still required
- Compare naming and description similarity between genuine and decoy items.
- Measure whether session-specific placement reduces simple fingerprinting.
- Evaluate multiple benign tasks and multiple overreaching behaviors.
- Report true positives, false positives, false negatives and limitations.
- Test reproducibility across Python/SDK versions.

## Claim boundary for the presentation
Say: “This prototype demonstrates a deterministic decoy-access detection pipeline using controlled simulated interactions.”
Do not say: “It detects all malicious MCP servers” or “evasion resistance is proven.”
