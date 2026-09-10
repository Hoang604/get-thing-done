---
name: propose-architecture
description: Propose macro architectural approaches for features or subsystems with trade-offs across topology, boundaries, and lifecycles
disable-model-invocation: true
---

# CORE DIRECTIVE

Conduct subsystem-scale architectural exploration and present exactly two viable, production-grade architectural approaches (`Approach A` versus `Approach B`) with explicit trade-offs.

Bypass planning mode entirely: do NOT create or update `implementation_plan.md` or ticket files. Output the complete architectural proposal, followed by the exact hard stop line, and pause execution.

---

## 1. Subsystem Discovery & Invariant Legwork

Explore the codebase across the target area to map existing boundaries, state lifecycles, and non-negotiable constraints before formulating designs.

### Architectural Invariant Definitions

- **Subsystem:** An autonomous unit of domain computation bounded by a singular conceptual model, encapsulating internal mechanics behind an explicit public interface.
- **Macro-Seam:** The structural boundary across which distinct subsystems exchange state, control, or lifecycle guarantees.
- **Bounded Context:** The domain perimeter within which data models, vocabulary, and operational rules maintain singular, uncorrupted meaning.
- **Load-Bearing Invariant:** A structural constraint, ordering guarantee, or state assertion that must remain true across all operations and transitions.

### Legwork Execution Protocol

1. Trace every existing subsystem and public entry point touched by the user request using `grep_search` and `view_file`.
2. Locate where relevant state originates, how it mutates, and where it terminates or settles.
3. Map existing boundaries, dependencies, and communication paths across the affected area.
4. Record every existing repository abstraction, convention, and design pattern to identify reuse opportunities.
5. Identify every load-bearing invariant that the new architecture must preserve without regression.

- **Completion Criterion**: Internal legwork mapping complete across touched subsystems, data flows, existing patterns, and non-negotiable invariants. Do not output intermediate dumps to chat; synthesize findings directly into the proposal in Step 3.

---

## 2. Systemic Forces & Quality Framing

Anchor candidate architectures in concrete engineering forces rather than subjective preference.

### Architectural Forces

- **Capacity Pressures:** Operational demands on resource throughput, temporal latency, or concurrent execution that penalize unified execution and necessitate structural boundaries.
- **Environmental Bounds:** Immutable host platform constraints, protocol specifications, or compatibility requirements that dictate boundary interfaces.
- **Failure Isolation:** Boundary perimeters that prevent internal faults, resource exhaustion, or invalid inputs from propagating into peer subsystems.

### Quality Tiers (Universal Scale)

Classify each candidate against the Quality Tiers (Tier 1 to 5, with a +0.5 bonus for utilizing existing repository patterns). Target Tier 5.5:

| Tier | Designation | Macro Architectural Signature |
|:---:|---|---|
| **5** | **Structural / Impossible** | Architecture makes failure and invalid states unrepresentable across boundaries through type systems, static contracts, or state machine topologies |
| **4** | **Systemic / Root-Cause** | Solves the generalized architectural invariant; enforces strict failure containment and unifies lifecycle management across subsystems |
| **3** | **Standard / Contract** | Complete subsystem implementation covering all specified functional requirements, contracts, and edge cases |
| **2** | **Narrow / Fragmented** | Leaky domain boundaries; requires multiple subsystems to coordinate manually with fragile temporal coupling |
| **1** | **Brittle / Workaround** | Superficial patching; shared mutable state across boundaries, unmanaged side effects, or circular dependencies |

#### Existing Pattern Alignment Modifier (+0.5 Tier Boost)
- **Award (+0.5)**: Apply to any approach that directly utilizes, conforms to, or extends established repository abstractions, conventions, or idioms instead of introducing foreign tooling or fragmented paradigms.
- **Justification**: Explicitly cite the existing repository pattern being reused and how it preserves conceptual integrity.

---

## 3. Formulate Architectural Approaches

Formulate exactly two distinct, viable, and production-ready architectural designs (`Approach A` versus `Approach B`). Both must be fully functional and engineering-sound. Treat both as viable solutions that an experienced principal engineer would strongly advocate for.

### The Two Architectural Archetypes

- **Approach A (Minimal Surface)**: The simplest architectural path that satisfies requirements by extending existing subsystems with minimal boundary modification, lowest moving parts, and maximum existing pattern reuse.
- **Approach B (Decoupled Topology)**: The cleanest, deeply isolated architecture optimized for boundary autonomy, strict failure containment, and independent subsystem evolution.

### Universal Architectural Principles

Evaluate both approaches against these generative principles:

- **Subsystem Depth:**
  - *Deep Subsystem*: Substantial internal domain capability shielded behind a small, focused public contract. Minimizes cognitive load and surface churn for callers.
  - *Shallow Subsystem*: Large, sprawling interface wrapping a thin pass-through implementation. Leaks internal mechanics and forces complexity into callers.
  - *The Deletion Test*: If a subsystem's internal implementation is completely rewritten or deleted, callers must remain unaffected. If changes cascade into callers, the boundary is shallow and must be rejected.
- **Macro-Seam Invariants:**
  - Seams are governed by three intrinsic axes:
    1. *Coupling Locality*: Intra-process memory references versus inter-boundary protocol serialization.
    2. *Temporal Coordination*: Immediate blocking execution versus deferred asynchronous processing.
    3. *State Determinism*: Reproducible internal calculation versus environmental interaction.
  - Interfaces expose semantic domain operations rather than raw storage schemas or transport wire representations.
  - Boundaries enforce bidirectional contract validation: incoming input is validated before entering domain logic; outgoing results conform to declared contracts.
- **Unidirectional State Flow:**
  - State moves along an explicit, directed path from stimulus through invariant validation and domain transition to terminal settlement.
  - Interfaces return explicit calculated outcomes or state transitions rather than mutating ambient caller state.
  - Illegal intermediate states are made structurally unrepresentable.
- **Independent Failure Containment:**
  - Subsystems must fail independently. A fault inside an auxiliary capability must not crash or deadlock the primary operational loop.

---

## 4. Proposal Presentation Contract

Deliver the entire architectural proposal as a single, cohesive presentation. Structure the response strictly as follows:

```markdown
# Architectural Proposal: <Feature or Subsystem Name>

## Context & Systemic Forces
- **Current Topology**: Concise summary of existing modules and demarcated responsibilities.
- **Technical Drivers & Constraints**: Primary non-functional forces and immutable constraints governing this change.
- **Non-Negotiable Invariants**: Structural guarantees and boundary rules that must remain intact.

---

## Approach A: <Descriptive Title> (Minimal Surface)

- **Quality Tier**: Tier rating (Tier 1 to 5.5) with pattern modifier and justification.
- **Suitable If**: The concrete production scenario or operational priority where this approach is the superior engineering choice.
- **Subsystem Topology & Boundaries**: Public interfaces versus encapsulated internal domain mechanics.
- **State Lifecycle & Data Flow**: Directed execution path from stimulus to terminal settlement.
- **Failure Domain & Blast Radius**: What can fail, how the fault is contained, and recovery behavior.
- **Pros & Cons**: Concrete engineering trade-offs in structural complexity, boundary coupling, and maintenance surface.
- **Principal Advocacy**: The strongest technical argument a principal engineer would make to defend this design.

---

## Approach B: <Descriptive Title> (Decoupled Topology)

- **Quality Tier**: Tier rating (Tier 1 to 5.5) with pattern modifier and justification.
- **Suitable If**: The concrete production scenario or operational priority where this approach is the superior engineering choice.
- **Subsystem Topology & Boundaries**: Public interfaces versus encapsulated internal domain mechanics.
- **State Lifecycle & Data Flow**: Directed execution path from stimulus to terminal settlement.
- **Failure Domain & Blast Radius**: What can fail, how the fault is contained, and recovery behavior.
- **Pros & Cons**: Concrete engineering trade-offs in structural complexity, boundary coupling, and maintenance surface.
- **Principal Advocacy**: The strongest technical argument a principal engineer would make to defend this design.

---

## Comparison Summary Table

| Dimension / Criterion | Approach A (<Name>) | Approach B (<Name>) |
|---|---|---|
| **Quality Tier** | Tier rating and pattern modifier | Tier rating and pattern modifier |
| **Suitable If** | Primary operational selection trigger | Primary operational selection trigger |
| **Subsystem Depth** | Public interface size versus internal mechanics | Public interface size versus internal mechanics |
| **Boundary Decoupling** | Coupling mechanism and boundary seams | Coupling mechanism and boundary seams |
| **State Flow Model** | State transition and settlement pipeline | State transition and settlement pipeline |
| **Failure Domain** | Blast radius perimeter and containment | Blast radius perimeter and containment |
| **Evolution Cost** | Effort and surface churn to extend | Effort and surface churn to extend |
| **Core Trade-off** | Primary concession accepted | Primary concession accepted |

<!-- Table Physical Contract: Strict single line per cell (1 to 8 words). Focus entirely on structural trade-offs without repeating paragraphs. -->
```

- **Completion Criterion**: Full proposal published matching the exact structure above, concluded by the exact Hard Stop line.

---

## 5. Hard Stop

Output exactly this line and stop calling tools or generating text:
`Please select an architectural approach or request modifications.`
