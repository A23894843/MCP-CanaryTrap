# Professor Presentation: Demo Script and Viva

## 5-minute demonstration
1. Explain MCP tools, resources and prompts using `server.py` and `client.py`.
2. Run tests: `python -m pytest -v`.
3. Run CLI: `python -m mcp_canarytrap.demo --scenario both`.
4. Show that benign returns `CLEAN`.
5. Show that overreaching returns `FLAGGED` and provides evidence event IDs.
6. Run `python -m mcp_canarytrap.api`, open `http://127.0.0.1:8000`, and use both dashboard buttons.
7. Explain the honest limitation: current harness simulates operations; live MCP traffic integration is future work.

## Viva questions
**Why deterministic instead of ML?** The proposed rule is explainable and reproducible: any decoy touch flags the session. It avoids training data and probabilistic thresholds, but depends on good decoy placement and instrumentation.

**What is a decoy?** A fabricated tool/resource/record with no legitimate reason to be accessed for the scripted task.

**What is the verdict rule?** No recorded decoy access means CLEAN; one or more decoy accesses means FLAGGED.

**What evidence supports FLAGGED?** The event IDs, timestamps, operation types and target names for the decoy interactions.

**Does FLAGGED prove malicious intent?** No. It proves only that the instrumentation recorded a decoy interaction. Context and test design still matter.

**Is the prototype connected to arbitrary MCP servers?** Not yet. It has a real MCP learning server/client plus a separate simulated harness. A live adapter/proxy and sandbox are needed.

**Why use SQLite?** It is simple, local and sufficient for a single-machine demonstrator. A production deployment would need stronger access controls, migrations, retention policies and concurrency testing.

**How is placement reproducible?** SHA-256 of the session ID provides a stable seed to shuffle decoys. This provides reproducibility, not secrecy against a knowledgeable adversary.

**What is the next research milestone?** A transport-aware MCP adapter in an isolated test environment, followed by a broader evaluation corpus and measured results.
