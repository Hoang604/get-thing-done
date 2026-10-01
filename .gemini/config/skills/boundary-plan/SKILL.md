---
name: boundary-plan
description: Draft sequential implementation plan driven by observable outcomes and boundary engineering decisions
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate any objective into a self-contained `implementation_plan.md` artifact ready for **zero-read execution**: once approved, coding proceeds without inspecting any additional files for context.
Structure execution not around arbitrary task tickets or isolated file diffs, but as a topological progression of **System Boundaries**.

Every boundary milestone is governed strictly by two invariant tiers:
1. **Observable Outcome:** What capability or state transition this boundary unlocks for the system, defined strictly by:
   > *"The observable outcome this boundary enables for the system, defined strictly by what it makes possible rather than how it operates."*
2. **Technical Decisions:** How this capability is materialized with maximal yield, defined strictly by:
   > *"Every technical decision serves solely to advance the system to a state possessing the new capability with maximal yield."*
   >
   > *Maximal yield pairs maximal delivered value with minimal system entropy.*

> [!IMPORTANT]
> **Minimal System Entropy is not minimal diff.**
> Diff measures transition cost; entropy measures structural disorder. A change achieves minimal entropy only when the resulting codebase has exactly one canonical way to represent and execute the concept, leaving zero structural residue from the transition.

The sum of all observable outcomes must compose cleanly into the complete objective.

---

## Maximal Yield Evaluative Lenses

When formulating technical decisions, evaluate every boundary against six authoritative architectural lenses:

1. **Abstraction Conservation:**
   *Anchors: Rich Hickey (Simple Made Easy) & Kent Beck (Once and Only Once / DRY)*
   Every existing mechanism in the system represents paid-down complexity. Solve problems by anchoring directly into established abstractions and conventions. Inventing parallel ad-hoc primitives or duplicating logic for problems the codebase already solves is forbidden.

2. **Seam Containment & Zero Blast Radius:**
   *Anchors: David Parnas (Information Hiding) & Michael Feathers (The Seam Model)*
   Confine all modifications hermetically behind an immediate seam. The ripple effect across external callers must be zero: callers interact through an invariant contract, ensuring the internal evolution of the boundary requires zero cascading edits elsewhere.

3. **Contract Honesty & Generative Boundaries:**
   *Anchors: Bertrand Meyer (Design by Contract) & Alexis King (Parse, Don't Validate)*
   Data crossing boundaries must be strictly verified into non-nullable domain types before reaching execution logic. Optionality is reserved exclusively for authorized business absence; untyped wildcards (`any`, `dict`) or surrogate fallback values masking broken contracts are strictly forbidden.

4. **Deep Modules & The Deletion Test:**
   *Anchors: John Ousterhout (A Philosophy of Software Design)*
   Maximize the ratio of encapsulated behavior to interface surface area. Reject shallow pass-through abstractions. Every introduced structure must pass the Deletion Test: if removing it causes complexity to collapse rather than reappear across callers, the structure is accidental complexity and must not exist.

5. **Open-Closed & State Hermeticity:**
   *Anchors: Bertrand Meyer (Open-Closed Principle) & Rich Hickey (Values over State)*
   Absorb behavioral variations additively through polymorphism or strategy composition rather than mutating existing control flow with procedural `if/elif` branching. Execution within the boundary must be causally deterministic: consuming injected dependencies and emitting calculated results without mutating ambient globals or caller state in-place.

6. **Caller Autonomy & High-Yield Design:**
   *Anchors: John Ousterhout (Deep Modules)*
   A boundary must maximize the power it provides to callers while keeping its interface minimal. Callers achieve their complete intent through a simple contract without managing callee state, coordinating internal sequencing, or creating parallel sources of truth.

---

## 1. Reality Anchoring & Scope Closure

Ground the plan in physical codebase reality before proposing modifications.

### Fixed-Point Scope Discovery
Starting from target entrypoints and interfaces, trace callers and consumers outward using `rg` and `view_file`.
- At each trace hop, determine whether the file requires changes.
- **Fixed-Point Criterion:** Scope discovery is complete when an additional trace hop produces no new files requiring changes:
  $$\text{Scope}_{k+1} = \text{Scope}_k$$

### Zero-Read Closed Scope Invariant
Every data type, structure, or interface crossing a boundary seam must have its physical definition fully bound within the plan context:
$$\text{Unbound References} = \emptyset$$
For read-only dependencies outside the mutation scope, extract their relevant structural definitions and inline them into the plan's context so execution requires zero secondary lookups.

**Completion Criterion:** An exhaustive manifest of affected files derived via fixed-point discovery, resolved definitions for all external references, and documented system invariants.

---

## 2. Topological Boundary Decomposition

Partition the objective into an ordered Directed Acyclic Graph (DAG) of system boundaries: $\{B_1, B_2, \dots, B_n\}$.

### Topological Enablement Rule
Execution order follows dependency topology. For every milestone $B_m$:
- All prerequisite capabilities, types, and seams required by $B_m$ must be fully established by prior milestones $\{B_1, \dots, B_{m-1}\}$.
- Every milestone $B_k$ (except terminal nodes) must unlock a necessary prerequisite state or capability for at least one downstream milestone in the DAG.

### Black-Box Capability Formulation
Formulate every milestone's **Observable Outcome** strictly by the generative standard:
> *"The observable outcome this boundary enables for the system, defined strictly by what it makes possible rather than how it operates."*

The state of the system at each boundary is defined exclusively by the stimuli it accepts and the verified responses it produces.

### Lineage Justification & Composability
- **Lineage & Justification:** Every milestone exists for an explicit reason: either directly fulfilling an authoritative requirement/goal, or providing an unavoidable prerequisite required to implement downstream milestones cleanly and correctly.
- **Composability Gate:** Verify that the union of all boundary outcomes strictly reconstitutes the total target scope:
  $$\bigcup_{k=1}^n \text{Outcome}(B_k) \equiv \text{Total Scope}$$

**Completion Criterion:** A topologically ordered sequence of boundaries where each milestone has documented lineage justification, satisfies topological enablement, and composes into the complete objective.

---

## 3. Boundary Milestone Anatomy

For every milestone in the DAG, declare the physical blueprint across two cohesive tiers:

### Tier 1: The System Boundary (What & Why)
- **Observable Outcome:** The precise system capability made possible by this boundary, defined strictly by what it makes possible rather than how it operates.
- **Acceptance Signal:** Anything that proves the declared observable outcome is verifiable and satisfied.
- **Provenance & Justification:** The direct goal this milestone fulfills, OR the prerequisite required to implement downstream milestones cleanly and correctly.

### Tier 2: Technical Decisions & Physical Contracts (How)
- **Key Decisions (10-Minute Review Standard):** Record the load-bearing engineering choices that satisfy the Maximal Yield Invariant across the evaluative lenses, articulated so a senior engineer with only 10 minutes can confidently approve the boundary before implementation begins.
  - *Minimal Entropy:* Decisions in this boundary to minimize system entropy.
  - *Maximal Value:* Decisions in this boundary to maximize delivered value.
- **Literal Contracts & Strict Types:** Declare literal non-nullable domain models and boundary interfaces crossing the seam (`class` / `def` signatures with complete type annotations, docstrings, and `...` ellipses method bodies).
- **Ingress Caller & Terminal Sink Audit:**
  - *Caller Audit (Ingress):* Audit all existing callers across the workspace. List every caller requiring updates, or certify: *"Caller Audit: 0 production callers found via search."*
  - *Terminal Sink Audit (Dataflow):* Trace return values, state mutations, or emitted events downstream to their terminal sink to prove data reaches its final destination.
- **File Manifest:** List every file affected using clickable links `[basename](file:///path#L1-L20)` demarcated with `[NEW]`, `[MODIFY]`, or `[DELETE]`.

---

## 4. In-Line Structural Anchor

Every `implementation_plan.md` begins with the overall strategy followed by the milestone sequence:

````markdown
## Minimal Entropy & Maximal Value Strategy

- **Minimal Entropy:** <Decisions made to achieve minimal entropy for the overall system>
- **Maximal Value:** <Decisions made to achieve maximal value for the overall objective>

### Milestone 1: <Descriptive Title>

- **Observable Outcome:** <What this boundary makes possible for the system or downstream milestones>
- **Acceptance Signal:** <Anything proving this outcome is verifiable and satisfied>
- **Provenance & Justification:** <Direct requirement fulfilled, or prerequisite enabling Milestone N>

#### Technical Decisions & Physical Contracts
- **Key Decisions:** <Load-bearing choices satisfying the Maximal Yield lenses, articulated for a 10-minute senior approval>
  - **Minimal Entropy:** <Decisions in this boundary to minimize system entropy>
  - **Maximal Value:** <Decisions in this boundary to maximize delivered value>
- **Literal Contracts & Bound Structures:**
  ```python
  class IngestionPayload(BaseModel):
      id: UUID
      event_type: EventType
      timestamp: datetime

  class IngestionPort(ABC):
      """Boundary interface for incoming payloads."""
      @abstractmethod
      async def ingest(self, payload: IngestionPayload) -> IngestionResult:
          ...
  ```
- **Caller & Sink Audit:**
  - Ingress: Called by `[WebhookController.handle](file:///src/controllers/webhook.py#L45)`
  - Terminal Sink: Persisted via `[EventStore.save](file:///src/storage/store.py#L88)`

#### File Mutations
- `[MODIFY]` [pipeline.py](file:///src/pipeline.py#L30-L65)
- `[NEW]` [strategy.py](file:///src/strategy.py)
````

---

## 5. Plan Artifact & Verification Gate

Compile the plan into `<Artifact Directory>/implementation_plan.md`.

### Verification Matrix
Specify baseline validation commands (typecheck, lint, unit tests, integration tests) to certify system invariants across all milestones.

### Subagent Dual Audit Directive
Embed the audit directive verbatim into `implementation_plan.md`.
**Single Variable Rule:** When invoking `boundary-auditor`, dispatch the exact prompt below without adding, modifying, or appending instructions. The only permitted dynamic value is substituting `<plan-link>` with the clickable file link `[implementation_plan.md](file:///path/to/implementation_plan.md)`.

````markdown
#### Subagent Spawn Directive (Post-Implementation)
> [!IMPORTANT]
> After completing all code implementation, spawn the standalone `boundary-auditor` subagent via `invoke_subagent`:
> - **TypeName**: `boundary-auditor`
> - **Role**: `Boundary Auditor`
> - **Prompt**: `Audit boundary implementation plan at <plan-link>. Execute your dual verification protocol and deliver audit_report.md to the directory containing <plan-link>.`
>
> *Invocation Contract:* Dispatch with this exact prompt. Do NOT append custom instructions, context summaries, or conversational steering.
````

### Convergence & Circuit Breaker Protocol
Declare execution bounds directly in `implementation_plan.md`:
- **Audit Budget:** Maximum 2 verification cycles. If verification fails on the second attempt, trigger an immediate **Hard Stop**.
- **Failure Dichotomy:** On Hard Stop, determine contract satisfiability before escalating:
  - **Design Flaw:** The boundary contract is unsatisfiable under system reality $\to$ Halt code mutation, revise the implementation plan.
  - **Reasoning Flaw:** The contract is satisfiable, but the implementation approach failed to converge $\to$ Fix the code within the established boundary.
