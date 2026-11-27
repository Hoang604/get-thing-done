---
name: boundary-plan
description: Draft sequential implementation plan driven by observable outcomes and boundary engineering decisions
---

# CORE DIRECTIVE

Translate any objective into a self-contained plan artifact ready for **zero-read execution**: once approved, coding proceeds without inspecting any additional files for context.
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
> **The Job Principle (Scope & Users):**
> Trace outward from every module the task touches along its callers and registration points for as long as those callers remain within the code the task permits creating or modifying (`mutable scope`). The outermost boundary where callers sit outside that mutable scope is the **entry boundary**, the boundary where results return across it is the **exit boundary**, and the external actors that invoke the entry boundary or consume what crosses the exit boundary are the **users**; code inside the mutable scope is the implementation, never a user.
> Each user's **job** is what that external actor is trying to get done across the mutable scope. Everything inside the mutable scope required for users to finish their jobs is in scope, including what the spec author left unwritten; anything serving a different job is out of scope.
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

**When** the user requests researching or creating an additional domain reference (via an autonomous web-search subagent or an external Deep Research prompt), read `references/domain-reference-research.md` to execute the reference-research protocol directly without generating `implementation_plan.md`.

**When** the system under design or modification involves realtime multi-user state synchronization, optimistic local mutations, collaborative documents, or stateful room coordination, read `references/realtime-sync.md` to evaluate and apply its synchronization primitives, plane segregation, and boundary invariants against the target system.

**When** the system under design or modification involves e-commerce checkout, order payment collection, payment webhooks, or customer refunds and cancellations, read `references/ecommerce-payment.md` to evaluate and apply its PCI scope contracts, durable idempotency rules, webhook fulfillment invariants, and refund state machine against the target system.

---

## 1. Intent Reconstruction & Reality Anchoring

Reconstruct the users and jobs behind the spec, then ground them in physical codebase reality. Both run together: the jobs tell legwork where to look, and the codebase tells the jobs what already exists.

### Users, Jobs & Use Scenarios
- **Users & Jobs:** Follow every outcome the spec describes outward to the entry and exit boundaries of the mutable scope (`The Job Principle`), and name every user outside that scope and the job it gets done, one line per user.
- **Use Scenarios:** Take each user's position outside the mutable scope, wanting only what that user wants and knowing only what that user knows. Walk the user's path across every state the product can be in when its job is attempted, and record each distinct path as a scenario: the literal stimulus the user sends across the mutable scope's entry boundary and the exact observable response the user receives across its exit boundary.
- **Observable Response:** What the user needs back across the mutable scope's exit boundary in that product state to finish its job, stated solely in terms that user outside the mutable scope already knows and written literally so that comparing it with a real run's output yields yes or no.
- **Invariants:** A scenario fixes one literal input; an invariant states the rule that holds for every input its product state admits from entry boundary to exit boundary. For every scenario whose response depends on its input, write the rules the response obeys for all such inputs, each so that one counter-input would prove it false, and name the scenarios it spans.
- **Implied Requirements:** Every requirement a scenario exposes that the spec leaves unwritten, each traced to the scenario that exposed it.

### Fixed-Point Scope Discovery
Starting from the entrypoints the scenarios pass through (or from the remaining targets in `## Open Investigations` when resuming an in-progress plan), trace callers and consumers outward using `rg` and `read_file`, inspecting every candidate slice with `read_file` before deciding its scope or contract. At each trace hop, determine whether the file requires changes: it requires changes when it breaks under the change, or when its form would fail the Day-One Test afterward. Scope discovery is complete when one more trace hop adds no file that needs changing.

### Retirement Inventory
For every concept the change touches, name its pre-change form: the exact names and shapes the change replaces or makes redundant. Search the whole workspace for each with `rg` and record every place whose content still depends on that form, not only its callers, each with its fate: deleted, rewritten to the new form, or kept with a justification drawn from present requirements alone.

### Zero-Read Closed Scope
Every type, structure, or interface crossing a seam has its definition written into the plan. For read-only dependencies outside the mutation scope, extract their relevant structural definitions and inline them so execution requires zero secondary lookups.

**Completion Criterion:** Every user named with its job; every user covered by at least one scenario; every reachable product state on each user's path present in at least one scenario as a literal invocation with its exact observable response; every scenario whose response depends on its input spanned by at least one invariant; implied requirements each traced to a scenario; an exhaustive manifest of affected files derived via fixed-point discovery; a Retirement Inventory in which every place still depending on a pre-change form has a fate; and resolved definitions for all external references.

---

## 2. Topological Boundary Decomposition

Partition the users' jobs into an ordered dependency graph of system boundaries: $B_1, B_2, \dots, B_n$.

### Caller Boundary Promotion vs. `Caller Audit`
For any caller $C$ inside the mutable scope that invokes a modified boundary $B$, test whether $C$ already holds values of the exact types $B$'s new signature requires, already receives the dependencies $B$ requires, and already translates every return value and error $B$ can produce into $C$'s own declared output:
- **When all three hold:** $C$ changes only its call expression and belongs in $B$'s `Caller Audit`.
- **When any of the three does not hold** ($C$ must construct or parse $B$'s input types, wire $B$'s dependencies, or handle/translate $B$'s return states or errors): test whether that work originates in $C$'s own responsibility or compensates for a detail $B$ exposed:
  - **Compensates for $B$:** redraw $B$ to absorb it so $C$ needs no such logic, then re-test $C$ above.
  - **Originates in $C$'s own responsibility:** $C$ is a distinct system boundary and must be assigned its own milestone with its own Tier 1 outcome, Tier 2 decisions, and `Literal Contracts` declaring $C$'s signature.

### Topological Enablement Rule
Execution order follows dependency order by topological level ($1, 2, \dots$). For every milestone $B_m$:
- All prerequisite capabilities, types, and seams required by $B_m$ must be fully established by strictly earlier levels.
- Every milestone except the last ones in the graph must unlock a necessary prerequisite for at least one later level.
- **Milestone Numbering:** Assign each milestone its topological level number (`1`, `2`, ...). When multiple milestones occupy the same level (no dependency between them), suffix them with uppercase letters (`1A`, `1B`, ...); when a level contains a single milestone, use the plain number (`1`, `2`, ...).

### Observable Outcome
Formulate every milestone's **Observable Outcome** by the standard stated in the Core Directive. The state of the system at each boundary is defined exclusively by the stimuli it accepts and the verified responses it produces.

### Lineage Justification & Composability
- **Lineage & Justification:** Every milestone exists for an explicit reason: either making one or more use scenarios runnable, or providing an unavoidable prerequisite required to implement later milestones cleanly and correctly.
- **Composability Gate:** Every use scenario is made runnable by exactly one milestone, and no milestone serves anything outside the users' jobs.

### Internal Module Architecture & Knowledge Uniqueness
- **Module & File Partitioning:** **When** partitioning code into files and modules within a milestone, identify every design decision likely to change independently and every existing or planned unit of behavior in scope (`file:line` or milestone target), and emit an individual ruling for each while holding the other units fixed before writing `Literal Contracts` or `File Manifest` (grouping items into a shared ruling is invalid): place in the same module only units that share the same design decision or cannot be understood independently without reading the other's internals; separate into distinct modules whenever units hide independent design decisions behind their own abstractions. Derive the milestone's target module layout and `File Manifest` strictly from these rulings so each module encapsulates a single cohesive design-decision cluster.
- **Ownership & Dependency Direction:** **When** assigning any responsibility to a module or establishing imports between modules in a milestone, list each relocated or new responsibility and each cross-module dependency edge touched or introduced by that milestone (`source -> target`, citing `file:line` or target symbol) individually, and emit a ruling on each while holding the other items fixed in the milestone's `Module & Edge Derivation` before writing `Literal Contracts` or `File Manifest` (grouping items into a shared ruling is invalid): place every responsibility in the module whose abstraction defines that concept—collapsing any boundary that introduces no distinct abstraction between its callers and callees—and orient every dependency edge as a directed acyclic graph pointing from volatile specific details toward stable policies or general-purpose abstractions, resolving any cycle or outward dependency before constructing `Literal Contracts` and `File Manifest` strictly from those rulings.
- **Canonical Knowledge Uniqueness:** **When** planning any change, inspect existing codebase primitives and peer flows in scope; for every piece of knowledge that **appears in multiple sites or resembles an existing codebase primitive or peer flow** (`file:line` for existing sites and target symbol/milestone for new code), emit an individual ruling while holding the other items fixed in `Canonical Knowledge Rulings` before the first milestone (grouping items into a shared ruling is invalid): consolidate into a single authoritative implementation inside its owning module whenever multiple occurrences express the same system knowledge that must change together; keep implementations separate without shared flags or branching abstractions whenever they only resemble each other syntactically while encoding independent decisions. Construct `Literal Contracts`, `Retired Forms`, and `File Manifest` strictly from those individual rulings.

**Completion Criterion:** An ordered sequence of boundaries where each milestone has documented lineage justification, satisfies topological enablement, no caller inside the mutable scope compensates for a detail an upstream boundary could absorb, every caller promoted by the Caller Boundary Promotion rule is assigned its own milestone, every use scenario is assigned to the milestone that makes it runnable, and the plan's `Canonical Knowledge Rulings` section before the first milestone emits an individual, coordinate-cited, non-grouped ruling for every multi-site or look-alike piece of knowledge.

---

## 3. Boundary Milestone Anatomy

For every milestone in the graph, declare the physical blueprint across two cohesive tiers:

### Tier 1: The System Boundary (What & Why)
- **Observable Outcome:** The precise system capability made possible by this boundary.
- **Acceptance Signal:** A literal invocation through the nearest real entrypoint and its exact observable response. A milestone that makes use scenarios runnable lists those scenarios and the invariants spanning them as its signal, invoked through the product's real entrypoint.
- **Provenance & Justification:** The use scenarios this milestone makes runnable, OR the prerequisite required to implement later milestones cleanly and correctly.

### Tier 2: Technical Decisions & Physical Contracts (How)
- **Module & Edge Derivation (Before Contracts & File Manifest):** Apply `Module & File Partitioning` to **every design decision and existing or planned behavioral unit** in this milestone and `Ownership & Dependency Direction` to **every responsibility and cross-module dependency edge** touched or introduced by this milestone before writing `Literal Contracts` or `File Manifest`.
- **Seam Derivation (Before Contracts):** Before writing `Literal Contracts`, derive the boundary from the inspected code and the scenarios or downstream milestone in `Provenance & Justification`:
  - *Caller Coupling (`Less to know` & `Friction`):* At each inspected caller (`file:line`) and across the scenarios `S-xx` (or downstream Milestone $N$) this milestone serves, list each distinct piece of caller code or user action required to use this boundary as its own item, and rule on each individually: **keep** when that caller's own job originates it, or **absorb** into the boundary (naming what owns it instead). Grouping multiple couplings into a shared ruling is invalid.
  - *Declaration Survival (`Deletion Test` & `Canonical Form`):* List each declaration exposed outside the boundary on the seam this milestone introduces or modifies as its own item, and rule on each individually while holding the other declarations fixed: name the single concept it represents, the pre-change forms it replaces, and the production callers outside the boundary (`file:line`, Milestone $N$, or `S-xx`) where complexity reappears if this declaration is removed from the boundary; drop or hide inside the boundary (recording any retired pre-change exposure in `Retired Forms`) every declaration with no production caller outside the boundary or whose removal leaves those callers no more complex. Grouping declarations into a shared ruling, or citing intra-boundary or test-only callers to keep a declaration exposed, is invalid.
- **Literal Contracts & Strict Types:** Declare strictly the declarations exposed outside the boundary that survived `Declaration Survival`, requiring nothing ruled **absorb** in `Caller Coupling`, written solely as type definitions and callable signatures with complete type annotations, docstrings, and `...` bodies. Declare an abstract interface only when the seam has more than one implementation under present requirements; otherwise the contract is the concrete function or class itself. Never include declarations hidden inside the boundary or implementation code beyond `...` bodies.
- **Ingress Caller & Terminal Sink Audit:**
  - *Caller Audit (Ingress):* Audit all existing callers across the workspace that pass the `Caller Audit` test above (requiring only a call-expression update). List every such caller, or certify: *"Caller Audit: 0 pure call-expression callers found via search."*
  - *Terminal Sink Audit (Dataflow):* Trace return values, state mutations, or emitted events downstream to their terminal sink to prove data reaches its final destination.
- **Retired Forms:** The Retirement Inventory entries this milestone makes obsolete, each at its location with its fate and the count of references that remain.
- **File Manifest:** List every file this milestone creates, modifies, or deletes as `[NEW]`, `[MODIFY]`, or `[DELETE]` with a clickable link `[basename](file:///path#L<start>-L<end>)` whose `#L<start>-L<end>` range spans the exact lines this milestone mutates.

**Completion Criterion:** Every milestone declares every field of both tiers; `Module & Edge Derivation` rules individually (without grouping) on every design decision/unit and on every responsibility and cross-module dependency edge touched or introduced by this milestone; `Caller Coupling` rules individually on every boundary interaction at the inspected caller `file:line` sites and served scenarios `S-xx` (or Milestone $N$); `Declaration Survival` rules individually on every declaration in `Literal Contracts` citing production callers outside the boundary; `Literal Contracts` contains only `Declaration Survival` survivors exposed outside the boundary, requires nothing ruled **absorb**, and uses `...` bodies with zero hidden helpers or implementation code; the owning module of each declaration in `Literal Contracts`, every file in `File Manifest`, and every consolidated or retired duplicate in `Retired Forms` match the milestone's `Module & Edge Derivation` and the plan's `Canonical Knowledge Rulings`; and every Retirement Inventory entry (including any pre-change exposure hidden inside the boundary) is resolved by the milestone that makes its form obsolete.

---

## 4. In-Line Structural Anchor & Verification Gate

Compile or finalize the initial plan in `<Artifact Directory>/implementation_plan.md` (`RequestFeedback: true` once `## Open Investigations` is empty and removed); for audit round `<N>`, write `<Artifact Directory>/implementation_plan_round_<N>.md` beside the prior plan (`RequestFeedback: false` during `execute`), starting at the top with a link to the prior plan and the prior-plan findings it resolves (inheriting the initial plan's `Audit Budget`). Every finalized plan begins with the users and their jobs, then the emitted canonical-knowledge rulings, then the milestone sequence, and ends with the verification matrix and subagent audit directive:
- **Audit Budget:** `<integer (default: 2) | unlimited>` — configures the maximum audit cycles before a Hard Stop. Set to `unlimited` to cycle until a clean pass or Plan Veto, or specify an integer limit (e.g., `1`, `3`).
- **Dynamic Parameter Rule:** Permitted substitutions in the `Subagent Spawn Directive` prompt are `<plan-link>`, `<N>` (the round number: `1, 2, ...`), and `<ledger-link>` (the `implementation_ledger.md` beside the plan).

````markdown
## Users, Jobs & Use Scenarios

- **Users & Jobs:**
  - <User outside mutable scope>: <The job this user gets done across the mutable scope, in one sentence>
- **Implied Requirements:** <Requirement the spec leaves unwritten> (exposed by S-xx)

| # | User | Product State | Invocation | Observable Response |
|---|---|---|---|---|
| S-01 | <User from the list above> | <The situation the user and product are in when the user acts> | `<Exact stimulus sent into the mutable scope's entry boundary>` | <Exact response received across the mutable scope's exit boundary> |

| # | Invariant | Spans |
|---|---|---|
| I-01 | <Rule that holds for every input the spanned scenarios' product state admits from entry boundary to exit boundary, stated so that one counter-input would prove it false> | S-01 |

## Canonical Knowledge Rulings

- `<multi-site or look-alike piece of knowledge at file:line / target milestones>`: <shared changing knowledge vs. independent decisions, holding other items fixed> -> **consolidate at <module/symbol>** | **keep separate**

### Milestone <N>[A|B...]: <Descriptive Title>

- **Observable Outcome:** <What this boundary makes possible for the system or later milestones>
- **Acceptance Signal:** <Scenarios S-xx made runnable and invariants I-xx spanning them, or a literal invocation and its exact observable response>
- **Provenance & Justification:** <Scenarios made runnable, or prerequisite enabling Milestone N>

#### Technical Decisions & Physical Contracts
- **Module & Edge Derivation:**
  - **Module Partitioning:** `<design decision or behavioral unit at file:line / target milestone>`: <shared vs. independent design decision & comprehensibility, holding other units fixed> -> **together in <module>** | **separate into <modules>**
  - **Ownership & Dependency Edge:** `<responsibility or edge A -> B at file:line / target milestone>`: <owning abstraction & DAG direction, holding other items fixed> -> **keep** | **resolve by <concrete structural change>**
- **Seam Derivation:**
  - **Caller Coupling:** <single caller interaction at file:line or user action in S-xx>: <originates in caller's job -> **keep** | absorbed by <owner> inside boundary -> **absorb**>
  - **Declaration Survival:** <single exposed declaration>: <concept & replaced pre-change form>; removing it from the boundary <complexity reappearing at production callers outside the boundary (file:line / Milestone N / S-xx)> -> **keep**
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
  - Ingress: `NoteController.create` at [notes.py](file:///src/controllers/notes.py#L45) must parse raw input into `NoteDraft` -> promoted to Milestone 2 (`0` pure call-expression callers)
  - Terminal Sink: Persisted via `[NoteRepository.insert](file:///src/storage/notes.py#L88)`
- **Retired Forms:**
  - `save_note(title, body, store=None)` at [notes.py](file:///src/controllers/notes.py#L52): deleted; call sites rewritten in Milestone 2; 0 references remain

#### File Manifest
- `[NEW]` [note_store.py](file:///src/note_store.py)

### Verification Matrix

- **Baseline Checks:** `<Automated validation commands (typecheck, lint, unit tests, integration tests) certifying system invariants across all milestones>`
- **Audit Budget:** `<integer (default: 2) | unlimited>`

#### Subagent Spawn Directive (Post-Implementation)
> [!IMPORTANT]
> After completing code implementation or remediation, spawn `boundary-auditor` via `invoke_subagent`:
> - **TypeName**: `boundary-auditor`
> - **Role**: `Boundary Auditor`
> - **Prompt**: `Audit boundary implementation plan at <plan-link> with implementation ledger at <ledger-link>. Execute your passive code inspection protocol and deliver audit_report_round_<N>.md.`
>
> *Invocation Contract:* Dispatch with this exact prompt structure. Do NOT append custom conversational steering.
````

### Approval Handoff (Chat Reply on `RequestFeedback: true`)
**When** finalizing the user-facing `implementation_plan.md` (`RequestFeedback: true`, zero `## Open Investigations`), deliver a decision-grade handoff in the chat reply—never inside `implementation_plan.md`, never on draft checkpoints (`RequestFeedback: false`), and never on `implementation_plan_round_<N>.md` (`RequestFeedback: false`)—structured strictly into three sections in order: (1) why to approve the plan, (2) choices where the user may decide differently or challenge the plan, and (3) what the user might want done that this plan deliberately does not do.

Before writing the handoff reply, evaluate individually while holding other items fixed:
1. **Plan commitments (for Sections 1 and 2):** every commitment `implementation_plan.md` makes or withholds whose alternative would visibly change either what the running system guarantees, exposes, or consumes beyond nominal scenarios (**real-world execution delta**) or what callers must adapt to, what adoption costs, or what viable alternative is foreclosed (**adoption and design-constraint delta**). **When** this evaluation exposes an avoidable weakness or hazard before finalizing `implementation_plan.md`, test whether it can be eliminated inside the mutable scope without sacrificing any scenario, invariant, or competing goal of the plan: if yes, revise `implementation_plan.md` to eliminate it before setting `RequestFeedback: true`. Route surviving high-confidence gains into **Section 1**, and route every surviving commitment where another viable choice, boundary, or premise exists (or an unavoidable trade-off remains) into **Section 2**, stating the plan's choice with its location, the assumption or reason behind it, and what alternative decision or challenge would change it.
2. **Excluded expectations (for Section 3, placed last):** every adjacent capability or workflow bordering the requested scope that was left outside `Users & Jobs` (`Section 1`). Include an exclusion in **Section 3** whenever someone making this request could plausibly expect that capability to be built or handled alongside the plan, stating directly what remains unimplemented or unchanged so the user can expand scope before approving.

Include an item across the three sections only when it carries a real decision, trade-off, or plausible unmet expectation grounded in the plan and scope, citing its plan location where applicable; omit unaffected areas and routine rule compliance that create no user choice.

**Completion Criterion:** The active plan file is finalized (`RequestFeedback` per Section 4), zero `## Open Investigations` remaining, every settled contract, caller/sink audit, retired form, and `#L<start>-L<end>` manifest backed by prior `read_file` inspection, and contains the users-and-jobs list, the scenario table, the invariant table, the `Canonical Knowledge Rulings` section before the first milestone, every milestone (including its `Module & Edge Derivation`), and the Verification Matrix (`Baseline Checks`, `Audit Budget`, and the verbatim `Subagent Spawn Directive`); and, when finalizing with `RequestFeedback: true`, every avoidable defect exposed during pre-handoff evaluation is resolved in `implementation_plan.md` before setting `RequestFeedback: true` and the chat handoff reply delivers all three sections in order—approval reasons, alternative decisions/challenges, and excluded expectations placed last—constructed strictly from those individual pre-handoff evaluations.

---

## 5. Compaction Checkpointing & Monotonic Resume

- **Pre-Compaction Draft Checkpoint:** **When** a context-budget warning or 1-step tool deferral arrives while any completion criterion above remains unmet, persist current planning state in that step to the active plan file in `<Artifact Directory>` (`write_file` on first checkpoint, `edit_file` on subsequent checkpoints) with `ArtifactMetadata` setting `UserFacing: true` and `RequestFeedback: false`, appending a `## Open Investigations` section for all unfinished discovery, and on the very next step continue dispatching the remaining `read_file` and `rg` calls until auto-compaction triggers (or finalize the active plan file by removing `## Open Investigations`, resolving any `[OPEN]` markers, and setting `RequestFeedback` per Section 4 once all open investigations resolve).
- **Settlement & Open-Investigation Partition:** **When** writing or updating the active plan file in `<Artifact Directory>`, ground every entry in code slices inspected with `read_file`:
  - **Each independent plan unit in scope:** Every independent unit in the plan—a plan-level section, an individual `Canonical Knowledge Rulings` entry, a milestone's Tier 1 block, its `Module & Edge Derivation`, its `Seam Derivation` paired with `Literal Contracts`, or an individual line in `Caller & Sink Audit`, `Retired Forms`, or `File Manifest`—depends solely on the upstream decisions and `read_file` slices that determine its own assertions (`Seam Derivation` and `Literal Contracts` depend on the boundary's implementation and external production boundary callers, whereas test files and pass-through callers govern only their own lines). **When** updating or checkpointing the active plan file, evaluate every unit in scope individually while holding the rest fixed: whenever all upstream decisions and `read_file` slices a unit depends on are inspected, write that unit literally into its place in the plan body; whenever any slice a unit depends on remains uninspected, mark that missing part `[OPEN: <what remains>]` inline inside a started milestone (or omit an unstarted unit from settled sections) and list its remaining `read_file`/`rg` targets in `## Open Investigations`.
  - **`## Open Investigations` content:** Record in `## Open Investigations` solely what uninspected `[OPEN]` parts still need: pair each remaining `read_file`/`rg` target with the exact `[OPEN]` plan unit it resolves, and retain an `Inspected (do not re-read)` entry (with `#L<start>-L<end>` and verbatim source facts passing the deleted-file check) only for already-inspected slices whose facts are still needed to finish an `[OPEN]` unit rather than repeating facts already written into the settled plan body. Keep one slice/target per bullet (no grouped files or prose file summaries).
  - *Anchor (partial milestone + `## Open Investigations` shape):*
    ```markdown
    - **Caller & Sink Audit:**
      - Ingress: `ApiHandler.create` at [api.py](file:///src/api.py#L40) -> Milestone 2
      - `[OPEN: inspect remaining callers in runner.py]`
    #### File Manifest
    - `[MODIFY]` [parser.py](file:///src/parser.py#L12-L48)
    - `[OPEN: test_parser.py line range]`

    ## Open Investigations
    - **Inspected (do not re-read):** `[parser.py](file:///src/parser.py#L12-L48)` — `parse(raw: str) -> Token` (`#L12`); raises `ParseError` if `not raw.strip()` (`#L18`) *(kept only if an `[OPEN]` unit still needs these details)*
    - **Remaining:** `[runner.py](file:///src/runner.py)` (`rg "parse\("` callers) — resolves Milestone 1 `Caller & Sink Audit`; `[test_parser.py](file:///tests/test_parser.py)` — resolves Milestone 1 `File Manifest` test line range
    ```
  - *Checkpoint Completion Criterion:* Every independent plan unit whose own upstream decisions and `read_file` slices are inspected sits literally in the settled plan body (without waiting on unread sibling items or test files); every still-uninspected part inside a started milestone carries an inline `[OPEN: ...]` marker; and `## Open Investigations` lists each remaining target paired with its `[OPEN]` unit plus `Inspected (do not re-read)` entries (one slice per bullet with `#L<start>-L<end>`, passing the deleted-file check) strictly for slices still needed by an `[OPEN]` unit.
- **Compaction `<summary>` Rules:** **When** the harness prompts for a compaction `<summary>` while `boundary-plan` governs the work, list in Section 2 (`Read-next working set`) this `SKILL.md` path (plus any active domain `references/*.md`), the active plan file path in `<Artifact Directory>`, and the next bounded batch of still-uninspected target slices from the open-investigation frontier (combining `## Open Investigations` on disk with any post-save additions recorded in Section 3) whose preconditions are met; in Section 3 (`Settled state and open work`), reference the active plan file without restating its contents and record verbatim every code detail and search result observed after the last write to that plan file, together with which `## Open Investigations` items and `[OPEN]` units those post-save observations resolved or added. Never place any slice already settled, already extracted in `## Open Investigations`, or already inspected after the last save into `Read-next working set`.
- **Post-Compaction Resume Rules:** **When** resuming `boundary-plan` after context compaction, remain in planning mode rather than executing code: read this `SKILL.md` (and any active domain `references/*.md`), the active plan file in `<Artifact Directory>`, and the uninspected slices in `<summary>`'s `Read-next working set` in a single batch. Treat every settled section and milestone part in the active plan file, every verbatim code detail already stored inside `## Open Investigations`, and every post-save observation in `<summary>` Section 3 as closed evidence of those code locations: fold any post-save observations from `<summary>` Section 3 into the active plan file via `edit_file` (settling any resolved `[OPEN]` parts into the plan body) on the first step after reading the draft (concurrently with the next open-investigation reads, or finalizing the plan immediately if no uninspected targets remain), and dispatch `read_file` and `rg` exclusively on the remaining uninspected targets until `[OPEN]` markers and `## Open Investigations` are empty. Never re-read a file slice or re-run an `rg` query whose required facts are already settled in the active plan file, stored in `## Open Investigations`, or recorded in `<summary>` Section 3.
