---
name: propose-plan
description: Gather context and propose architectural approaches with clear trade-offs
disable-model-invocation: true
---

# CORE DIRECTIVE

Conduct thorough research and present distinct architectural approaches with trade-offs.
Draft strictly architectural approaches and trade-offs. Output the exact stop line and pause execution.

---

## 1. Gather Context (Exhaustive Legwork)

Explore codebase to identify all direct dependencies, imports, and caller interfaces affected by the user request.

- **Completion Criterion**: You must list every read target file, direct import, and calling function. Trace dependencies recursively until hitting external system boundaries or core libraries.

---

## 2. Frame Reality

- Document current behavior, system constraints, and technical drivers.
- List exact core files and shared modules impacted.
- Identify **invariants**: load-bearing boundaries and data structures that must remain unchanged.

- **Completion Criterion**: Output a unified list explicitly stating current behavior, system constraints, exact impacted files, and load-bearing invariants.

---

## 3. Propose Approaches

Provide exactly two distinct, viable approaches (`Approach A` vs `Approach B`) satisfying all requirements. Both MUST be functional and engineering-sound; Propose exactly two distinct, viable, and production-ready designs. Construct the strongest possible case for both approaches. Treat both as viable solutions that an experienced engineer would strongly advocate for.

- **Approach A (Pragmatic / Minimalist)**: The simplest, fastest implementation path that completely fulfills the requirements with minimal moving parts or surface-area modification.
- **Approach B (Architectural / Robust)**: The cleanest, most extensible and scalable architecture, optimized for long-term maintenance, clean seams, and modularity.

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

- **Pros**: Evaluate advantages in module depth, seam complexity, and performance.
- **Cons**: Evaluate disadvantages in module depth, seam complexity, and performance.
- **User Outcomes**:
  - After this task, user should be able to `<do something specific>`
  - After this task, user should see `<specific observable result>`
- **Senior Engineer Advocacy**: Explicitly state why an experienced engineer would fight for this approach.

- **Completion Criterion**: Output exactly two approaches (`Approach A` and `Approach B`). Each approach must explicitly contain the headings: `Pros`, `Cons`, `User Outcomes`, and `Senior Engineer Advocacy`.

---

## 4. Hard Stop

Output exactly this line and stop calling tools or generating plan text:
`Please select an approach or request modifications.`
