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
   >
   > *Maximal value means every user finishes its **job** without friction.*

> [!IMPORTANT]
> **The Job Principle (Scope Definition):**
> The **users** are everything that consumes an outcome of what the spec describes: whatever invokes it and whatever receives what it produces. A user is not necessarily a person; programs that call it, parse its output, or read what it stores are users too. Each user's **job** is what it is trying to get done with that outcome.
> Scope is the users' jobs, not the sentences of the spec. Everything the users need to finish their jobs is in scope, including what the spec author left unwritten. Anything that serves a different job is out of scope.
> **Friction** is any moment where a user must know, guess, or do something its job does not require.

> [!IMPORTANT]
> **Minimal System Entropy is not minimal diff.**
> Diff measures transition cost; entropy measures structural disorder. A change achieves minimal entropy only when the resulting codebase has exactly one canonical way to represent and execute the concept, leaving zero structural residue from the transition.
>
> **The Day-One Test:**
> Everything the change touches or makes obsolete must take the form it would have had if the system had been designed for its current requirements from day one. Any form whose justification needs the code's past instead of the system's present requirements is **residue**. A boundary milestone is complete only when it leaves no residue.

The sum of all observable outcomes must compose cleanly into every user's complete job.

---

## Maximal Yield Principle

Every technical decision answers to one principle:

> **Each change leaves everything outside the boundary with less to know and less to change than before.**

Outside the boundary is anything that interacts with it without seeing inside it, the users included.

- **Less to know.** A boundary's interface is everything a caller must know to use it correctly. Keep that equal to what its signature states: if correct use requires knowing anything the signature does not say, the boundary leaks. The strongest boundary does a great deal of work behind a signature that tells the whole truth.
- **Less to change.** When behaviour later varies or evolves, the change lands inside the boundary and code outside stays as it is. This judges the shape the change leaves behind, never the size of the change itself: edits outside the boundary that remove a pre-change form are what the Day-One Test demands.
- **The Deletion Test.** For every structure the change introduces, imagine deleting it. If complexity reappears across its callers, the structure earns its place. If complexity collapses, the structure was accidental and must not exist.

Reuse of what the system already has is governed by Minimal System Entropy above (exactly one canonical way); type and contract rigor by the global type safety and invariant policies. This principle restates neither.

---

## 1. Intent Reconstruction & Reality Anchoring

Reconstruct the users and jobs behind the spec, then ground them in physical codebase reality. Both run together: the jobs tell legwork where to look, and the codebase tells the jobs what already exists.

### Users, Jobs & Use Scenarios
- **Users & Jobs:** Follow every outcome the spec describes to whatever invokes it and whatever receives it; each of those is a user. Name every user and the job it gets done, one line per user.
- **Use Scenarios:** Take each user's position in turn: want only what that user wants and know only what that user knows, setting aside what the spec author intends and what the implementer knows about the internals. From that position, walk the user's path across every state the product can be in when its job is attempted, and record each distinct path as a scenario: a literal stimulus through the product's real entrypoint and the exact observable response that user receives.
- **Observable Response** is the literal text, value, or error the user receives, written so that comparing it with the real response yields yes or no.
- **Invariants:** A scenario fixes one literal input; an invariant states the rule that holds for every input its product state admits. For every scenario whose response depends on its input, write the rules the response obeys for all such inputs, each so that one counter-input would prove it false, and name the scenarios it spans.
- **Implied Requirements:** Every requirement a scenario exposes that the spec leaves unwritten, each traced to the scenario that exposed it.

### Fixed-Point Scope Discovery
Starting from the entrypoints the scenarios pass through, trace callers and consumers outward using `rg` and `view_file`. At each trace hop, determine whether the file requires changes: it requires changes when it breaks under the change, or when its form would fail the Day-One Test afterward. Scope discovery is complete when one more trace hop adds no file that needs changing.

### Retirement Inventory
For every concept the change touches, name its pre-change form: the exact names and shapes the change replaces or makes redundant. Search the whole workspace for each with `rg` and record every place whose content still depends on that form, not only its callers, each with its fate: deleted, rewritten to the new form, or kept with a justification drawn from present requirements alone.

### Zero-Read Closed Scope
Every type, structure, or interface crossing a seam has its definition written into the plan. For read-only dependencies outside the mutation scope, extract their relevant structural definitions and inline them so execution requires zero secondary lookups.

**Completion Criterion:** Every user named with its job; every user covered by at least one scenario; every reachable product state on each user's path present in at least one scenario as a literal invocation with its exact observable response; every scenario whose response depends on its input spanned by at least one invariant; implied requirements each traced to a scenario; an exhaustive manifest of affected files derived via fixed-point discovery; a Retirement Inventory in which every place still depending on a pre-change form has a fate; and resolved definitions for all external references.

---

## 2. Topological Boundary Decomposition

Partition the users' jobs into an ordered dependency graph of system boundaries: $B_1, B_2, \dots, B_n$.

### Topological Enablement Rule
Execution order follows dependency order. For every milestone $B_m$:
- All prerequisite capabilities, types, and seams required by $B_m$ must be fully established by earlier milestones.
- Every milestone except the last ones in the graph must unlock a necessary prerequisite for at least one later milestone.

### Observable Outcome
Formulate every milestone's **Observable Outcome** by the standard stated in the Core Directive. The state of the system at each boundary is defined exclusively by the stimuli it accepts and the verified responses it produces.

### Lineage Justification & Composability
- **Lineage & Justification:** Every milestone exists for an explicit reason: either making one or more use scenarios runnable, or providing an unavoidable prerequisite required to implement later milestones cleanly and correctly.
- **Composability Gate:** Every use scenario is made runnable by exactly one milestone, and no milestone serves anything outside the users' jobs.

**Completion Criterion:** An ordered sequence of boundaries where each milestone has documented lineage justification, satisfies topological enablement, and every use scenario is assigned to the milestone that makes it runnable.

---

## 3. Boundary Milestone Anatomy

For every milestone in the graph, declare the physical blueprint across two cohesive tiers:

### Tier 1: The System Boundary (What & Why)
- **Observable Outcome:** The precise system capability made possible by this boundary.
- **Acceptance Signal:** A literal invocation through the nearest real entrypoint and its exact observable response. A milestone that makes use scenarios runnable lists those scenarios and the invariants spanning them as its signal, invoked through the product's real entrypoint.
- **Provenance & Justification:** The use scenarios this milestone makes runnable, OR the prerequisite required to implement later milestones cleanly and correctly.

### Tier 2: Technical Decisions & Physical Contracts (How)
- **Key Decisions (10-Minute Review Standard):** Record the load-bearing engineering choices, argued through Minimal System Entropy and the Maximal Yield Principle, so a senior engineer with only 10 minutes can confidently approve the boundary before implementation begins.
  - *Minimal Entropy:* How each touched concept keeps exactly one canonical form, what callers no longer need to know, and which pre-change forms this milestone retires.
  - *Maximal Value:* Choices that remove friction from this milestone's scenarios, each tied to the scenario state it serves.
- **Literal Contracts & Strict Types:** Declare literal non-nullable domain models and boundary interfaces crossing the seam (`class` / `def` signatures with complete type annotations, docstrings, and `...` ellipses method bodies). Declare an abstract interface only when the seam has more than one implementation under present requirements; otherwise the contract is the concrete function or class itself.
- **Ingress Caller & Terminal Sink Audit:**
  - *Caller Audit (Ingress):* Audit all existing callers across the workspace. List every caller requiring updates, or certify: *"Caller Audit: 0 production callers found via search."*
  - *Terminal Sink Audit (Dataflow):* Trace return values, state mutations, or emitted events downstream to their terminal sink to prove data reaches its final destination.
- **Retired Forms:** The Retirement Inventory entries this milestone makes obsolete, each at its location with its fate and the count of references that remain.
- **File Manifest:** List every file affected using clickable links `[basename](file:///path#L1-L20)` demarcated with `[NEW]`, `[MODIFY]`, or `[DELETE]`.

**Completion Criterion:** Every milestone declares every field of both tiers, every Maximal Value decision names the scenario state it serves, and every Retirement Inventory entry is resolved by the milestone that makes its form obsolete.

---

## 4. In-Line Structural Anchor

Every `implementation_plan.md` begins with the users and their jobs, then the overall strategy, then the milestone sequence:

````markdown
## Users, Jobs & Use Scenarios

- **Users & Jobs:**
  - <User>: <The job this user gets done, in one sentence>
- **Implied Requirements:** <Requirement the spec leaves unwritten> (exposed by S-xx)

| # | User | Product State | Invocation | Observable Response |
|---|---|---|---|---|
| S-01 | <User from the list above> | <The situation the user and product are in when the user acts> | `<Exact command, request, or call the user makes>` | <Exact output, return value, or error the user receives> |

| # | Invariant | Spans |
|---|---|---|
| I-01 | <Rule that holds for every input the spanned scenarios' product state admits, stated so that one counter-input would prove it false> | S-01 |

## Minimal Entropy & Maximal Value Strategy

- **Minimal Entropy:** <How each touched concept keeps one canonical form, what callers no longer need to know, and which pre-change forms are retired, across the whole system>
- **Maximal Value:** <Decisions that remove friction across the users' jobs, each tied to the scenarios it serves>

### Milestone 1: <Descriptive Title>

- **Observable Outcome:** <What this boundary makes possible for the system or later milestones>
- **Acceptance Signal:** <Scenarios S-xx made runnable and invariants I-xx spanning them, or a literal invocation and its exact observable response>
- **Provenance & Justification:** <Scenarios made runnable, or prerequisite enabling Milestone N>

#### Technical Decisions & Physical Contracts
- **Key Decisions:** <Load-bearing choices argued through Minimal System Entropy and the Maximal Yield Principle, articulated for a 10-minute senior approval>
  - **Minimal Entropy:** <Canonical form kept, knowledge removed from callers, pre-change forms retired>
  - **Maximal Value:** <Friction removed from scenario S-xx and how>
- **Literal Contracts & Bound Structures:**
  ```python
  @dataclass(frozen=True)
  class NoteDraft:
      title: NonEmptyStr
      body: str

  def save(draft: NoteDraft) -> SavedNote:
      """Persist the draft and return it with its assigned id."""
      ...
  ```
- **Caller & Sink Audit:**
  - Ingress: Called by `[NoteController.create](file:///src/controllers/notes.py#L45)`
  - Terminal Sink: Persisted via `[NoteRepository.insert](file:///src/storage/notes.py#L88)`
- **Retired Forms:**
  - `save_note(title, body, store=None)` at [notes.py](file:///src/controllers/notes.py#L52): deleted; its 3 call sites rewritten to `note_store.save`; 0 references remain

#### File Mutations
- `[MODIFY]` [notes.py](file:///src/controllers/notes.py#L30-L65)
- `[NEW]` [note_store.py](file:///src/note_store.py)
````

---

## 5. Plan Artifact & Verification Gate

Compile the plan into `<Artifact Directory>/implementation_plan.md`.

### Verification Matrix
- **Baseline Checks:** Validation commands (typecheck, lint, unit tests, integration tests) certifying system invariants across all milestones.
- **Dogfood Scenarios:** The full use scenario table, which execution runs through the product's real entrypoint after building.
- **Invariant Probes:** The full invariant table, which execution probes through the product's real entrypoint with the inputs most likely to break each invariant.

### Subagent Dual Audit Directive
Embed the audit directive verbatim into `implementation_plan.md`.
**Dynamic Parameter Rule:** Permitted substitutions in the prompt are `<plan-link>`, `<N>` (the round number: 1, 2, ...), and `<ledger-link>` (the `implementation_ledger.md` beside the plan).

````markdown
#### Subagent Spawn Directive (Post-Implementation)
> [!IMPORTANT]
> After completing code implementation or remediation, spawn `boundary-auditor` via `invoke_subagent`:
> - **TypeName**: `boundary-auditor`
> - **Role**: `Boundary Auditor`
> - **Prompt**: `Audit boundary implementation plan at <plan-link> with implementation ledger at <ledger-link>. Execute your passive code inspection protocol and deliver audit_report_round_<N>.md to the directory containing <plan-link>.`
>
> *Invocation Contract:* Dispatch with this exact prompt structure. Do NOT append custom conversational steering.
````

### Convergence & Circuit Breaker Protocol
Declare execution bounds directly in `implementation_plan.md`:
- **Audit Budget:** `<integer (default: 2) | unlimited>`
  - Configures the maximum audit cycles before a Hard Stop. Set to `unlimited` to cycle until a clean pass or Plan Veto, or specify an integer limit (e.g., `1`, `3`).
- **Plan Veto Escalation:** When the auditor determines that the plan is architecturally flawed or conceived as a patch that cannot be made permanent and residue-free, halt execution immediately without producing `walkthrough.md` and escalate directly to the user with the auditor's findings. Do not attempt autonomous remediation.

**Completion Criterion:** `implementation_plan.md` exists with the users-and-jobs list, the scenario table, and the invariant table, the strategy, every milestone, the Verification Matrix (baseline checks, dogfood scenarios, and invariant probes), the verbatim Subagent Spawn Directive, and the declared Audit Budget.
