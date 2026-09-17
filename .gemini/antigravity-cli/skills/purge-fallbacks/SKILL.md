---
name: purge-fallbacks
description: Reference criteria distinguishing invariant-corrupting state fabrication from contract-authorized defaults.
disable-model-invocation: true
---

# Invariant Integrity: State Fabrication vs. Contractual Defaults

A software boundary is a **validation membrane**, never a **state fabricator**.

A downstream consumer lacks the structural authority to invent state. State originates exclusively at the producer and must satisfy structural invariants before admission.

## 1. The Generative Principle

Every value transition across a boundary evaluates to a binary outcome:
- **Admit**: The incoming state fully satisfies the structural contract $\rightarrow$ pass through untouched.
- **Reject**: The incoming state violates the structural contract or required state is missing $\rightarrow$ fail fast immediately.

Substituting a synthetic value at the point of consumption to evade rejection is **State Fabrication**. It converts a fail-fast invariant violation into silent state corruption.

## 2. Structural Classification

### State Fabrication (Defensive Masking)
State fabrication occurs whenever a consumer synthesizes data to compensate for an upstream breach of contract.

- **Invariant Erasure**: Suppressing an invalid or missing required state instead of terminating execution at the failure boundary.
- **Lineage Inversion**: Defining fallback semantics at the downstream consumer rather than enforcing completeness at the upstream producer.
- **Temporal Falsification**: Substituting dummy structures in place of pending asynchronous state instead of preserving the explicit unready lifecycle.

### Contractual Defaults (Legitimate Absence)
A default is legitimate if and only if absence is a first-class semantic state explicitly authorized by the contract.

- **Contractual Provenance**: The default value and its fallback semantics are defined by the authoritative contract or schema, not synthesized ad-hoc by the consumer.
- **Boundary Anchoring**: Resolution occurs at the ingress or configuration boundary, establishing canonical state before entering the domain.
- **Semantic Neutrality**: The default represents the deliberate, complete absence of optional state, not the surrogate repair of corrupted or missing required state.

## 3. The Structural Boundary Test

Evaluate any fallback against the structural contract:

1. **Contract Authority**: Does the authoritative contract declare the field optional, with this exact default defined as its canonical representation? If the field is required for domain integrity, any consumer-side fallback is state fabrication.
2. **Lineage Ownership**: Is the fallback positioned at the ingress boundary where state is initially ingested, or downstream where state is consumed? Downstream consumers must assert invariants, not fabricate defaults.
3. **Failure Semantics**: Does the absence of this value indicate that an upstream invariant was violated? If yes, the boundary must reject immediately.
