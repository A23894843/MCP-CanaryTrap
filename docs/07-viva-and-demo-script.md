# Professor Presentation: Demo Script and Viva

## 5-minute demonstration
1. Explain MCP tools, resources and prompts using `server.py` and `client.py`.
2. Run tests: `python -m pytest -v`.
3. Run CLI: `python -m mcp_canarytrap.demo --scenario both`.
4. Show that benign returns `CLEAN`.
5. Show that overreaching returns `FLAGGED` and provides evidence event IDs.
6. Run `python -m mcp_canarytrap.api`, open `http://127.0.0.1:8000`, and use the built-in scenario buttons.
7. Demonstrate Custom test builder: change the decoy target name, add an interaction to that exact target, and show `FLAGGED`; then run a case that never touches a configured decoy and show `CLEAN`. This proves the cases are configurable rather than a fixed list of scenario names.
8. Explain the honest limitation: custom tests use structured simulated events; live MCP traffic integration and natural-language case interpretation are not implemented.

## Viva questions
**Why deterministic instead of ML?** The proposed rule is explainable and reproducible: any decoy touch flags the session. It avoids training data and probabilistic thresholds, but depends on good decoy placement and instrumentation.

**What is a decoy?** A fabricated tool/resource/record with no legitimate reason to be accessed for the scripted task.

**What is the verdict rule?** No recorded decoy access means CLEAN; one or more decoy accesses means FLAGGED. In custom mode, the backend derives decoy access by exact, case-insensitive matching against the examiner-configured decoy target registry.

**What evidence supports FLAGGED?** The event IDs, timestamps, operation types and target names for the decoy interactions.

**Does FLAGGED prove malicious intent?** No. It proves only that the instrumentation recorded a decoy interaction. Context and test design still matter.

**Is the prototype connected to arbitrary MCP servers?** Not yet. It has a real MCP learning server/client plus a separate simulated harness. A live adapter/proxy and sandbox are needed.

**Why use SQLite?** It is simple, local and sufficient for a single-machine demonstrator. A production deployment would need stronger access controls, migrations, retention policies and concurrency testing.

**How is placement reproducible?** SHA-256 of the session ID provides a stable seed to shuffle decoys. This provides reproducibility, not secrecy against a knowledgeable adversary.

**Can an examiner invent a new test case?** Yes. The custom test builder accepts a new case name, decoy targets, and structured interactions without editing the source code. The rule engine remains the same. A free-text description is contextual only; the verdict uses the structured interactions.

**What is the next research milestone?** A transport-aware MCP adapter in an isolated test environment, followed by a broader evaluation corpus and measured results.
