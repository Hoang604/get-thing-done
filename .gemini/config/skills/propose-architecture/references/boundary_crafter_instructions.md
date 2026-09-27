# CORE DIRECTIVE

Conduct thorough research and present distinct architectural approaches with trade-offs for this assigned boundary.
Draft strictly architectural approaches and trade-offs. This request does NOT warrant a plan. You must bypass planning mode entirely. Do NOT create or update any `implementation_plan.md` artifact.
During exploration and auditing, author your working drafts in artifact storage (`<appDataDir>/brain/<subagent-id>/draft_proposal.md`).
Upon final single-approach convergence, deliver the final proposal to `.gtd/<task-name>/<node_name>/proposal.md` and the exported contract to `.gtd/<task-name>/<node_name>/contract.md`.

---

## 1. Context Ingress & Boundary Legwork

1. **Immediate Ingestion**: Read the assigned task file and all referenced files concurrently as your starting point.
2. **Trace Dependencies**: Discover and read affected files, callers, and invariants recursively within your assigned boundary, stopping at direct external interfaces.

- **Completion Criterion**: List every inspected target file, direct import, and calling interface.

---

## 2. Frame Reality

- Document current behavior, system constraints, and technical drivers.
- List exact core files and shared modules impacted.
- Identify **invariants**: load-bearing boundaries and data structures that must remain unchanged.

- **Completion Criterion**: Output a unified list explicitly stating current behavior, system constraints, exact impacted files, and load-bearing invariants.

---

## 3. Circuit-Breaker Protocol (Escalation Gate)

Halt execution if what the task and its referenced files demand cannot be reconciled with the codebase without breaking a foundational invariant (or if the referenced files contradict each other).

### Escalation Action
1. Immediately halt all further drafting and tool calls.
2. Send an escalation message directly to the Orchestrator with strictly this structure:
   - **Contradiction**: the assertion that broke against codebase reality.
   - **Evidence**: `file:line` citations proving the contradiction.
   - **Decision**: the exact choice required from human.
3. Pause execution and wait for human resolution via the Orchestrator.

---

## 4. Propose Approaches

Provide exactly two distinct, viable approaches (`Approach A` vs `Approach B`) satisfying all requirements. Both MUST be functional and engineering-sound; Propose exactly two distinct, viable, and production-ready designs. Construct the strongest possible case for both approaches. Treat both as viable solutions that an experienced engineer would strongly advocate for.

- **Approach A (Pragmatic / Minimalist)**: The simplest, fastest implementation path that completely fulfills the requirements with minimal moving parts or surface-area modification.
- **Approach B (Architectural / Robust)**: The cleanest, most extensible and scalable architecture, optimized for long-term maintenance, clean seams, and modularity.

### Quality Tiers (Universal)

Classify each candidate against the Quality Tiers (Tier 1–5, with a +0.5 bonus for utilizing existing system patterns), strictly preferring **5.5 > 5 > 4.5 > 4 > 3.5 > 3 > 2.5 > 2 > 1.5 > 1**. Default is Tier 5 thinking:

| Tier | Name | Signature (Features & Fixes Alike) |
|---|---|---|
| **5** | **Structural / Impossible** | Changes design so failure/invalid states *cannot exist* |
| **4** | **Systemic / Root-Cause** | Solves the generalized invariant; covers the entire class of scenarios and lifecycles |
| **3** | **Standard / Contract** | Complete implementation covering all specified requirements and edge cases with tests |
| **2** | **Narrow / Ad-Hoc** | Special-cases only observed scenarios; brittle at boundaries or unhandled variations |
| **1** | **Brittle / Workaround** | Superficial workaround; obscures symptom or works by accident |

#### Existing Pattern Alignment Modifier (+0.5 Tier Bonus)
- **Existing Pattern Bonus (+0.5)**: Award a +0.5 tier boost (e.g., Tier 3 → Tier 3.5, Tier 4 → Tier 4.5) to any approach that directly utilizes, conforms to, or extends existing system patterns, idioms, established abstractions, and conventions instead of introducing foreign mechanisms or fragmented paradigms.
- **Bonus Justification**: When applying the +0.5 boost, explicitly cite the existing codebase pattern, utility, or architectural convention being reused and how it preserves conceptual integrity.

Evaluate both valid trade-off paths against these self-contained design principles:

- **Module Depth & Deletion Test (`Deep vs Shallow`):**
  - **Exact Terminology (`Module & Interface`):**
    - **Module:** Anything with an interface and an implementation (`scale-agnostic: function, class, package, or tier-spanning slice`). Use precise terminology restricted to: module, function, class, package, or tier-spanning slice.
    - **Interface:** Everything a caller must know to use the module correctly. Define interface as the complete contract: type signature, invariants, ordering constraints, error modes, required configuration, and performance characteristics.
  - Design **deep modules**: lots of behavior hidden behind a small interface (`fewer methods, simple params`). Reject **shallow modules** (`large interface, thin pass-through implementation`).
  - **Side-Effect Rejection:** Interfaces must return calculated results (`pure outputs`) rather than mutating caller/global state. Inject all external adapters strictly as parameters.
  - **The Deletion Test:** Imagine deleting the module. If complexity reappears across N callers, it earned its keep; if complexity vanishes without loss, it was a shallow pass-through and must be rejected.
- **Seams & Dependency Categorization:**
  - A **seam** is where the interface lives. **One adapter means a hypothetical seam; two adapters means a real one.** Introduce seams strictly when justified by at least two adapters or distinct dependency types.
  - **Internal vs External Seams:** A deep module can have private internal seams for its own implementation and tests. Keep all internal seams strictly private within the module.
  - Classify seam dependencies: `In-process` (`pure compute/memory -> merge modules, no adapter`), `Local-substitutable` (`local stand-in like PGLite -> test with stand-in`), `Remote-owned` (`define port, in-memory test adapter`), or `True-external` (`injected port + mock adapter`).
- **Decoupled & Open-Closed (`Isolation seams`):**
  - Seams and interfaces must operate and evolve in isolation. Abstractions must actively decouple the system, else they should not exist.
  - **Open-Closed:** The system must absorb new features strictly by adding new code. If adding a new variant forces mutating old code, the contract fails this rule.
- **Concrete Patterns:**
  - Name exact design patterns. If a pattern exists solely for speculative future-proofing or creates concurrency/I/O bottlenecks, it is an anti-pattern and fails.

For each approach, explicitly list:

- **Quality Tier**: Label as Tier 1–5 (with `+0.5` modifier if utilizing existing system patterns, e.g., `Tier 4.5`) with rationale. If implementing below Tier 4 (base tier), explicitly state the constraint or blocker preventing a higher tier.
- **Suitable If**: State the exact real-world scenario, future feature requirement, or operational priority where this approach wins. Use concrete scenario anchors rather than abstract adjectives.
- **Pros**: Evaluate advantages in module depth, seam complexity, and performance.
- **Cons**: Evaluate disadvantages in module depth, seam complexity, and performance.
- **User Outcomes**:
  - After this task, user should be able to `<do something specific>`
  - After this task, user should see `<specific observable result>`
- **Senior Engineer Advocacy**: Explicitly state why an experienced engineer would fight for this approach.

### Comparison Summary Table

Conclude the working draft with an executive comparison table contrasting Approach A and Approach B.

**Table Construction Contract:**
- **Cell Density:** Single line per cell (1–8 words). Use concrete metrics, tags, and deltas.
- **Content Focus:** Classify architectural differences without restating prose.

| Dimension / Criterion | Approach A (Pragmatic / Minimalist) | Approach B (Architectural / Robust) |
|---|---|---|
| **Quality Tier** | Tier 3 (Standard + Existing Pattern) | Tier 5.5 (Structural / Impossible) |
| **Suitable If** | Fixed to 1 provider, fast internal MVP | Multi-provider expansion, dynamic runtime swapping |
| **Module Depth** | Shallow (3 helper classes, leaky params) | Deep (1 facade function, private state) |
| **Seams & Decoupling** | In-process (tightly coupled to DB driver) | Remote-owned (isolated behind port interface) |
| **Implementation Scope** | 2 files modified (~40 LOC) | 5 files modified / 1 new module (~180 LOC) |
| **Long-term Maintenance** | Moderate (callers must handle error states) | High (invalid states unrepresentable) |
| **Core Trade-off** | Fast delivery, but leaks domain logic | Higher upfront effort, but zero downstream churn |

- **Completion Criterion**: Output exactly two approaches (`Approach A` and `Approach B`) in the preliminary working draft. Each approach must explicitly contain the headings: `Quality Tier`, `Suitable If`, `Pros`, `Cons`, `User Outcomes`, and `Senior Engineer Advocacy`. Conclude with the structured `Comparison Summary Table` contrasting both approaches.

---

## 5. Inner Convergence Loop & Final Delivery

1. **Initial Draft Delivery (Artifact Storage)**:
   - Author your preliminary dual-approach architectural proposal (`Approach A` vs `Approach B`, with each approach explicitly defining its candidate exported contract) exclusively to the subagent artifact directory:
     `<appDataDir>/brain/<subagent-id>/draft_proposal.md`

2. **Adjudication & Convergence**:
   - Spawn an `architecture-adjudicator` instance via `invoke_subagent`:
     - `TypeName`: `architecture-adjudicator`
     - `Role`: `Architecture Adjudicator`
     - `Prompt`:
       `Adjudicate draft proposal at: <appDataDir>/brain/<subagent-id>/draft_proposal.md with task context: <task-file-path>`
   - Evaluate the adjudicator report:
     - **If CIRCUIT_BREAKER_TRIGGERED**: Immediately halt execution and escalate contradiction to the Orchestrator with the artifact link the adjudicator give you.
     - **If Approach Selected**: Adopt the winning approach and any required contract adjustments. Kill the adjudicator subagent via `manage_subagents`.

3. **Final Single-Approach Convergence & Workspace Delivery**:
   - Author `.gtd/<task-name>/<node_name>/proposal.md` by reusing your draft proposal: prune the discarded approach, and convert the comparison table into an `Architectural Profile` list for the selected approach.
   - Author the exported boundary contract to:
     `.gtd/<task-name>/<node_name>/contract.md` containing strictly the public interface of this boundary: everything an external caller needs to know to integrate with it, and nothing internal.
   - Reply to the orchestrator with strictly this single confirmation line:
     `Completed: Final proposal and contract delivered on .gtd/<task-name>/<node_name>/proposal.md and .gtd/<task-name>/<node_name>/contract.md`
