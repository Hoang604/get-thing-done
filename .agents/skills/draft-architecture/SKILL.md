---
name: draft-architecture
description: Write the confirmed architectural approach into a permanent, deterministic ./.gtd/<task_name>/ARCHITECTURE.md blueprint
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved architectural approach from `propose-architecture` into a permanent, deterministic `./.gtd/<task_name>/ARCHITECTURE.md` blueprint on disk using `write_to_file`.

Do not re-explore alternative approaches. Bypass planning mode entirely: do NOT create `implementation_plan.md` or ticket files. Enforce literal architectural contracts (typed interfaces, schemas, state machine definitions, data flow pipelines, and failure boundaries) in the target codebase's primary implementation language. Method bodies MUST be strictly stubs. Never leak line-by-line implementation code into the blueprint.

This document serves as the single source of truth and architectural anchor for downstream ticket decomposition via `/req-to-tickets` or `/to-ticket`.

---

## 1. Guardrail & Scope Verification

Before drafting, verify prerequisites and establish execution boundaries:

### Prerequisites & Definitions

- **Task Scope:** The concise, kebab-case identifier denoted as `<task_name>` for this feature or subsystem. Derived from user arguments, active context, or existing `.gtd/` directory structure.
- **Architectural Selection Guardrail:** Execution requires an explicit user selection of an architectural approach from a prior `propose-architecture` invocation.
  - *Violation Handling:* If no approach has been locked by the user, HALT immediately and output:
    `[GUARDRAIL]: No architectural approach selected. Please run /propose-architecture and select an approach before running /draft-architecture.`
- **Target File Path:** The output blueprint must be written directly to `./.gtd/<task_name>/ARCHITECTURE.md` on disk.

- **Completion Criterion**: Confirmed locked architectural approach, verified `<task_name>`, and initialized directory `./.gtd/<task_name>/`.

---

## 2. Gather Context & Codebase Grounding

Inspect codebase conventions to ground the blueprint in real repository patterns:

1. Extract the selected approach name, quality tier justification, and accepted trade-offs from the conversation history.
2. Read the definitions of existing domain models, boundary interfaces, and shared utilities in the affected area using `view_file` and `grep_search`.
3. Map the precise module paths where new abstractions, types, and seams will live.

- **Completion Criterion**: Every touched module, domain entity, boundary interface, and shared utility in the affected area inspected. Context grounded in existing codebase vocabulary.

---

## 3. Author `./.gtd/<task_name>/ARCHITECTURE.md`

Write the complete architectural blueprint directly to `./.gtd/<task_name>/ARCHITECTURE.md` on disk using `write_to_file`. Enforce the exact structure below:

````markdown
# Architecture Blueprint: <Feature or Subsystem Name>

## 1. Executive Context & Decision Record (ADR)
- **Problem Statement & Drivers**: The core technical drivers and system forces requiring this architecture.
- **Selected Approach**: The chosen approach name and its assigned Quality Tier.
- **Principal Rationale**: The architectural defense for why this approach was selected, citing existing codebase patterns reused.
- **Accepted Trade-offs**: The operational, complexity, or migration trade-offs explicitly accepted.
- **Non-Negotiable Invariants**: The structural guarantees and state invariants that must never be broken.

---

## 2. Subsystem Topology & Bounded Contexts

### Topology Diagram
```mermaid
%%{init: {"flowchart": {"defaultRenderer": "elk"}}}%%
graph TD
  %% Directed graph showing bounded contexts, public entry points, data stores, and communication pathways
```

### Subsystem Boundaries & Depth
- **Subsystem Name**: `<Name>`
  - **Public Surface**: The minimal facade, protocol, or interface exposed to callers.
  - **Hidden Domain Mechanics**: The internal entities, mappers, algorithms, and validation shielded from external callers.
  - **Deletion Test Boundary**: How this subsystem can be removed or rewritten without forcing cascading changes across callers.

---

## 3. Boundary Seams & Type Contracts

> [!IMPORTANT]
> Author all signatures and schemas in the primary implementation language of the target repository, employing native typing constructs.
> Method bodies MUST be strictly stubbed. Never write line-by-line implementation code.

### Public Seams & Interfaces
```<target_language>
// Literal public interface contracts and protocols governing boundary entry points
```

### Core Data Models & Schemas
```<target_language>
// Literal domain schemas, value objects, enums, and state models
```

### Boundary & Persistence Contracts
- **State Settlement Contracts**: Literal signatures governing state storage, retrieval, or serialization where applicable.
- **Boundary Ports**: Literal signatures governing interactions with external or peer subsystems.

---

## 4. State Lifecycle & Data Flow Topology

### Directed Execution Pipeline
The ordered sequence of operations moving state from stimulus to terminal settlement:
1. **Stimulus Reception & Boundary Validation**: Trigger ingestion, schema verification, and structural invariant assertions.
2. **Domain State Transition**: Invariant evaluation and atomic state mutation boundaries.
3. **State Settlement**: Committing mutations to internal or external storage sinks where applicable.
4. **Result Propagation**: Returning calculated results or emitting downstream notifications.

### State Machine & Invariant Matrix
- **Permitted States**: The complete enumeration of valid system states.
- **State Transition Matrix**:
  | Current State | Trigger / Event | Next State | Invariant Enforced |
  |---|---|---|---|
  | `<State>` | `<Event>` | `<NextState>` | `<Invariant that must hold>` |
- **Illegal State Elimination**: The structural mechanism preventing invalid states from being represented.

### Fault Settlement & Invariant Recovery
- **Failure Recovery Protocol**: The deterministic protocol executed when state transitions fail midway.
- **State Consistency Assurance**: Mechanism ensuring data remains uncorrupted and invariants hold during partial failures.

---

## 5. Failure Domains & Blast Radius Containment

- **Fault Isolation Perimeter**: The boundary within which errors, panics, and unexpected states are contained.
- **Degradation & Fallbacks**: The explicit fallback behavior executed when dependencies become unavailable.
- **Typed Error Hierarchy**:
  ```<target_language>
  // Literal typed exceptions, error enums, or failure unions in the target language
  ```

---

## 6. Downstream Execution Roadmap (Tracer-Bullet Slices)

Decompose the architecture into sequential, vertically sliced phases ready to be consumed by `/req-to-tickets` or `/to-ticket`. Each phase must represent an independently verifiable vertical slice cutting through all necessary layers:

- [ ] **Phase 1: <Descriptive Slice Title>**
  - **Milestone Value**: The independently verifiable capability delivered by this vertical slice.
  - **Primary Seams**: Clickable markdown links to exact target files.
  - **Anticipated Blast Radius**: Clickable markdown links to related files.
  - **Acceptance Signal**: Observable verification proof demonstrating the slice works end-to-end.
- [ ] **Phase 2: <Descriptive Slice Title>**
  - **Milestone Value**: The next verifiable vertical capability delivered.
  - **Primary Seams**: Clickable markdown links to exact target files.
  - **Anticipated Blast Radius**: Clickable markdown links to related files.
  - **Acceptance Signal**: Observable verification proof demonstrating the slice works end-to-end.
- [ ] **Phase 3: <Descriptive Slice Title>**
  - **Milestone Value**: The next verifiable vertical capability delivered.
  - **Primary Seams**: Clickable markdown links to exact target files.
  - **Anticipated Blast Radius**: Clickable markdown links to related files.
  - **Acceptance Signal**: Observable verification proof demonstrating the slice works end-to-end.
````

- **Completion Criterion**: File `./.gtd/<task_name>/ARCHITECTURE.md` is authored to disk using `write_to_file` and verified against the template structure.

---

## 4. Completion & Downstream Hand-off

Output a concise summary and clear next-action instructions:

```markdown
### Architecture Blueprint Published (`./.gtd/<task_name>/ARCHITECTURE.md`)

- **Selected Approach:** `<Approach Name>` (Quality Tier `<Tier>`)
- **Subsystem Boundaries:** `<Summary of encapsulated modules>`
- **Execution Phases:** `<N> vertical tracer-bullet phases defined`

**Next step:** Run `/req-to-tickets` or `/to-ticket` to decompose this architecture blueprint into executable tickets in `./.gtd/<task_name>/tickets/`.
```

Stop calling tools or generating additional text.
