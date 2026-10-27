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
