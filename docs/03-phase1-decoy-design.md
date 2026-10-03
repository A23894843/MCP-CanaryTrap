# Phase 1 Decoy Design

The synopsis proposes three categories:

1. fabricated high-privilege tools
2. fabricated sensitive data assets
3. fabricated high-value records

The prototype models these as safe Python design objects; it does not perform destructive actions or contain real secrets.

## Placement scaffold

A session ID is hashed to create a reproducible seed and the decoy list is shuffled. This is only a research scaffold. The synopsis requires session-varying placement and resistance to fingerprinting; stronger strategies must be researched and evaluated in later phases.

## Research questions

- Can a server identify a decoy from metadata?
- Can placement patterns be learned across sessions?
- What metadata must be varied?
- How do we guarantee a benign task never needs a decoy?
- What evidence proves exactly which decoy was touched?
