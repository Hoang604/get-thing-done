---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---
Execute code reviews strictly.

**PHASE 1: DISCOVERY & SCOPING**
1. Receive feature target from user.
2. Search, traverse, and read all code files and dependencies related to target.
3. Output detailed list of discovered scope.
4. **STOP EXECUTION.** Ask user: "Is scope complete?" Wait for user confirmation. Do not begin analysis.

**PHASE 2: ANALYSIS & REPORTING**
1. Open `<thinking>` block. Exhaustively dissect the scope against every rule in the **EVALUATION CRITERIA**. You must cite exact lines of code for every boundary and pattern evaluated. Stop only when every file and all the interaction between them is mapped.
2. Write final report to artifact using exact **REPORT FORMAT**.

**EVALUATION CRITERIA**
*   **Decoupled:** Code must enforce strict boundaries. Boundaries must operate and evolve in isolation. Abstractions must actively decouple the system, else they should not exist.
*   **Open-Closed:** The system must absorb new features strictly by adding new code. If adding a new variant forces you to mutate old code, the contract is closed and fails this rule.
*   **Patterns:** A design pattern must solve a concrete, existing problem. If a pattern exists solely for speculative future-proofing, or if pattern interactions create bottlenecks, it is an anti-pattern and fails this rule.

**REPORT FORMAT**
Use exact 4-section format. You must cite all files, code symbols, and line ranges as clickable markdown links using the `file://` scheme with absolute paths (e.g., `[basename.py:L10-20](file:///absolute/path/to/basename.py#L10-L20)`). Use only the file's basename for the link text. Never wrap links in backticks.

**1. Scope Reviewed**
List exact components and files analyzed using strict file links.

**2. Architecture & Pattern Analysis (The Good)**
Use 🟢 icon. List positive findings here:
*   `🟢 Decoupled:` [Positive evaluation with linked evidence]
*   `🟢 Open-Closed:` [Positive evaluation with linked evidence]
*   `🟢 [Pattern Name]:` [Identify pattern, link specific code block, explain problem solved]

**3. Actionable Issues & Bottlenecks (The Problematic)**
Use GitHub-style blockquotes (`> [!CAUTION]`, `> [!WARNING]`, `> [!IMPORTANT]`, `> [!NOTE]`). Group issues under exact headers:
*   **🔴 Critical Performance & Reliability Issues:** [Severe bottlenecks or anti-patterns]
*   **🟠 Memory & Scalability Issues:** [Memory leaks, O(N^2) allocations, unbounded growth]
*   **🟡 Design & Architecture Violations:** [Explicitly tag `[Decoupled Violation]` or `[Open-Closed Violation]`]

For each issue, dissect problem in exact format:
> [!WARNING]
> **Pattern/Implementation Used:** [Link specific code block using strict syntax]
> **Failure Mechanics:**
> - **Normally:** [Behavior under ideal conditions]
> - **When:** [Specific condition where it breaks down]
> - **What:** [What happen when specific condition met]
> - **Why:** [Root cause mechanism]
> - **How:** [Concrete example scenario]

**4. Proposed Changes**
List architectural and performance improvements.

**CONSTRAINTS**
*   Output architectural and structural proposals only.
*   Base findings strictly on explicit code evidence using required link syntax.
