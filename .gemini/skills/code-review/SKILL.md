---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---
Execute code reviews strictly.

**GLOSSARY & CORE VOCABULARY**
Use these exact terms when analyzing code and reporting findings:
*   **Module**: Anything with an interface and an implementation (function, class, package).
*   **Interface**: Everything a caller must know to correctly use the module (signatures, invariants, ordering constraints, error modes, configuration, performance characteristics).
*   **Implementation**: What sits inside a module (`body of code`).
*   **Depth**: Amount of behavior hidden behind a unit of interface. **Deep module** = small interface + large implementation. **Shallow module** = large interface + thin pass-through.
*   **Seam**: Location where an interface lives and behavior can be altered/swapped without editing that place.
*   **Adapter**: Concrete role satisfying an interface at a seam (`in-memory fake`, `Postgres repo`).
*   **Leverage & Locality**: Leverage gives callers more capability per interface unit. Locality concentrates bugs, changes, and verification inside one place.

**PHASE 1: DISCOVERY & SCOPING**
1. Receive feature target from user.
2. Search, traverse, and read all code files, dependencies, and existing tests related to target.
3. Output detailed list of discovered scope and boundaries.
4. **STOP EXECUTION.** Ask user: "Is scope complete?" Wait for user confirmation. Do not begin analysis.

**PHASE 2: ANALYSIS & REPORTING**
1. Open `<thinking>` block. Exhaustively dissect the scope against every rule in **EVALUATION CRITERIA** and **DEPENDENCY & DEEPENING ASSESSMENT**. You must cite exact lines of code for every module, seam, adapter, and test boundary evaluated. Stop only when every file and all interaction across seams is mapped.
2. Call tool `write_to_file` to save final report artifact to `<appDataDir>/brain/<conversation-id>/<report-name>.md` using exact **REPORT FORMAT**. Outputting markdown stream to chat response does not satisfy completion criterion.

**EVALUATION CRITERIA**
*   **Deep vs Shallow Modules (The Deletion Test):** Code must form deep modules. Apply the **deletion test**: imagine deleting the module. If complexity vanishes, it is a shallow pass-through (`[Shallow Pass-through]`). If complexity reappears across N callers, it earned its keep (`Deep`).
*   **Seam Discipline & Adapter Count:** A seam must exist only when behavior genuinely varies across it. One adapter means a hypothetical seam (`[Hypothetical Seam]`); two adapters (`production + test stand-in/mock`) justify a real seam. Do not expose internal implementation seams through the external interface just for tests.
*   **Test Surface & Testability:** The external interface is the sole test surface. Callers and tests must cross the exact same seam. If tests assert internal state or require mocking in-process details (`testing past the interface`), tag `[Test Surface Violation]`. Modules must:
    1. *Accept dependencies, do not create them* inside the body (`[Hardcoded Dependency]`).
    2. *Return results, do not produce side effects* (`[Side-Effect Mutation]`).
    3. *Maintain small surface area* (fewer methods and parameters).
*   **Open-Closed:** The system must absorb new features strictly by adding new code. If adding a new variant forces mutation of existing code, tag `[Open-Closed Violation]`.
*   **Patterns:** A design pattern must solve a concrete, existing problem. If a pattern exists solely for speculative future-proofing, or creates indirection bottlenecks, it is an anti-pattern.

**DEPENDENCY & DEEPENING ASSESSMENT**
Classify dependencies to evaluate architectural boundaries and propose refactors:
1. **In-process**: Pure computation, in-memory state, no I/O. Must be merged into deep modules and tested directly through the unified interface without ports/adapters.
2. **Local-substitutable**: Dependencies with local test stand-ins (`PGLite`, `in-memory filesystem`). Seam must remain internal; test with the stand-in running in the suite without exposing external ports.
3. **Remote but owned (Ports & Adapters)**: Internal services across network boundaries. Require a port (`interface`) at the seam with an HTTP/gRPC adapter for production and an in-memory adapter for testing.
4. **True external (Mock)**: Third-party services (`Stripe`, `Twilio`). Require an injected port and a mock adapter in tests.
5. **Replace, Don't Layer:** Old unit tests on shallow modules are waste once tests at the deepened interface exist. Refactors must replace them with tests asserting observable outcomes at the seam.

**REPORT FORMAT**
Use exact 4-section format. You must cite all files, code symbols, and line ranges as clickable markdown links using the `file://` scheme with absolute paths (e.g., `[basename.py:L10-20](file:///absolute/path/to/basename.py#L10-L20)`). Use only the file's basename for the link text. Never wrap links in backticks.

**1. Scope Reviewed**
List exact components and files analyzed using strict file links.

**2. Architecture & Pattern Analysis (The Good)**
Use 🟢 icon. List positive findings here:
*   `🟢 Deep Module / Leverage:` [Identify deep interface hiding complexity with linked evidence]
*   `🟢 Clean Seam / Real Adapter:` [Justified seam with production + test variation]
*   `🟢 Open-Closed:` [Positive evaluation with linked evidence]
*   `🟢 [Pattern Name]:` [Identify pattern, link specific code block, explain problem solved]

**3. Actionable Issues & Bottlenecks (The Problematic)**
Use GitHub-style blockquotes (`> [!CAUTION]`, `> [!WARNING]`, `> [!IMPORTANT]`, `> [!NOTE]`). Group issues under exact headers:
*   **🔴 Critical Performance & Reliability Issues:** [Severe bottlenecks or anti-patterns]
*   **🟠 Memory & Scalability Issues:** [Memory leaks, O(N^2) allocations, unbounded growth]
*   **🟡 Design & Architecture Violations:** [Explicitly tag `[Shallow Pass-through]`, `[Hypothetical Seam / Unnecessary Indirection]`, `[Test Surface Violation]`, `[Hardcoded Dependency]`, `[Side-Effect Mutation]`, or `[Open-Closed Violation]`]

For each issue, dissect problem in exact format:
> [!WARNING]
> **Pattern/Implementation Used:** [Link specific code block using strict syntax]
> **Failure Mechanics:**
> - **Normally:** [Behavior under ideal conditions]
> - **When:** [Specific condition where it breaks down]
> - **What:** [What happens when specific condition met]
> - **Why:** [Root cause mechanism / failing deletion test / wrong seam]
> - **How:** [Concrete example scenario]

**4. Proposed Changes**
List architectural and performance improvements.
*   Must classify dependencies (`In-process`, `Local-substitutable`, `Remote-owned`, `True-external`) when proposing boundary modifications.
*   Must explicitly state whether old tests on shallow layers should be deleted (`Replace, don't layer`) and where the new test surface sits.

**CONSTRAINTS**
*   Output architectural and structural proposals only.
*   Base findings strictly on explicit code evidence using required link syntax.
*   Must invoke `write_to_file` to write report to physical file in artifacts directory. Streamed markdown text in chat response does not count as completed report.
