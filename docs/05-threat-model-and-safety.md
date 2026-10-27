# Threat Model, Assumptions and Safety

## Protected objective
Detect interactions with decoys that a scripted task has no legitimate reason to access.

## Assumptions in this prototype
- The event producer correctly marks whether the target is a decoy.
- The session ID is correctly attached to each event.
- The decoy list is known to the evaluator.
- The test uses fabricated data and runs locally.

## Threats considered conceptually
- Over-broad enumeration of available tools/resources.
- Attempts to access fabricated high-privilege tools.
- Attempts to read fabricated sensitive assets or high-value records.
- Basic fingerprinting by name and ordering.

## Out of scope for this prototype
- Monitoring an arbitrary external MCP server without an adapter.
- Authentication/authorization enforcement for a production multi-user service.
- Protection against a fully informed adversary who knows the decoy generator.
- Proving malicious intent from one access.
- Production-grade sandboxing and network/filesystem isolation.

## Safe demo behavior
All decoys are fictional strings. No real credentials, destructive tools, real payroll data or confidential business records are used. The simulation does not execute the fabricated administrative tool.

## False-positive nuance
A decoy touch is a deterministic signal under this policy, but a real evaluation must ensure decoys are never presented as legitimate task requirements. A bad task design or mistaken instrumentation could create a misleading flag.
