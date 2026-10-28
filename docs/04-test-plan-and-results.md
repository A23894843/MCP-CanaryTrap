# Test Plan and Expected Results

Run: `python -m pytest -v`

## Automated checks
1. The decoy taxonomy contains all three required categories.
2. Placement is reproducible for a given session ID.
3. An empty session ID is rejected.
4. A benign simulation returns `CLEAN` and contains no decoy events.
5. An overreaching simulation returns `FLAGGED` and includes evidence IDs for three decoy touches.
6. The session verdict can be retrieved from SQLite after the run.

## Expected demo matrix
| Scenario | Genuine events | Decoy events | Expected verdict |
|---|---:|---:|---|
| Benign | 2 | 0 | CLEAN |
| Overreaching | 2 | 3 | FLAGGED |

## Interpretation
These tests validate the programmed demonstration and deterministic policy. They do not measure real-world false-positive rates, detection rates, latency, server compatibility or evasion resistance. Those require a real MCP integration and a broader independently designed test corpus.


## Custom-case regression tests
The custom test suite checks that (1) a new examiner-defined target configured as a decoy produces `FLAGGED`, (2) a custom session with no matching decoy access produces `CLEAN`, (3) matching is case-insensitive but exact, and (4) invalid interactions are rejected before a session is persisted. These are controlled unit tests, not measurements of real-world MCP detection performance.

## Live gateway regression coverage
The current gateway test suite also covers HTTP upstream configuration validation, dashboard save/activate and non-secret status reporting, a mocked MCP initialize handshake, injection into `tools/list` / `resources/list` / `prompts/list`, decoy interception without forwarding to the upstream, SSE frame transformation, and a subprocess-level stdio proxy test. Latest local run: **27 passed, 1 skipped**. The skipped test requires the MCP SDK integration environment and is not evidence of a failure.

These are unit/integration tests using controlled or mocked upstreams. They do not replace compatibility testing against real third-party MCP implementations or an independent security assessment.
