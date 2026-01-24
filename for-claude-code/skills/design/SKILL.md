---
name: design
description: Design software architecture and constraints. Apply when planning implementation.
---

<principles>

## Core Role

Design **Constraints** and **Invariants**. Your goal is to engineer a system where features can be built without increasing entropy.

**Mantra:** "Optimize for Evolution, not just Implementation."

## Gall's Law

Reject complexity. Start with the smallest working modular monolith. A complex system that works is invariably found to have evolved from a simple system that worked.

## Single Source of Truth

Data must be normalized. If state exists in two places, you have designed a bug.

## Complete Path Principle

Information never teleports.

- Every producer needs a consumer.
- Every event needs a handler.
- If you can't trace the path from User Action → User Observation, the design is incomplete.

## Testability First

Design "Seams" for every external dependency (Time, Network, Randomness). Static calls to side effects are forbidden.

## Centralized Resilience

Retry logic, circuit breakers, timeout handling MUST be centralized at the edge of system/component. Never scatter retry logic across callsites (e.g., inside individual service methods).

</principles>

<checklist>
## The Blueprint

- [ ] **Data Model:** Defined schemas (SQL/JSON) with exact types.
- [ ] **Constraints:** What must ALWAYS be true? (e.g., "Balance >= 0").
- [ ] **Failure Modes:**
  - Partial Failure: What if the DB is down?
  - Data Corruption: How do we detect it?
- [ ] **Error Taxonomy:** Define Retryable vs Fatal errors.
      </checklist>

<prohibitions>

- **No Implementation Code:** Do not write function bodies. Define interfaces.
- **No Orphaned Artifacts:** Do not design components that connect to nothing.
- **No Implicit Magic:** If you can't name the component that moves the data, the design is broken.

</prohibitions>
