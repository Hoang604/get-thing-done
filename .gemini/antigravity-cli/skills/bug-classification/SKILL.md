---
name: bug-classification
description: Classify bugs into Local Implementation Faults vs Architectural Seam Defects based on seam sufficiency
disable-model-invocation: true
---

# Bug Classification

Classify input bugs into two groups based on **Seam Sufficiency**:

1. **`LOCAL`**: The seam is sound. The defect is an internal implementation error behind the seam.
2. **`ARCHITECTURAL`**: The seam is inadequate. Satisfying requirements is impossible without altering the seam or forcing defensive workarounds across callers.

---

## 1. Decision Principle

- **Seam**: Where the interface lives — everything a caller must know and rely upon to use a module correctly.
- **Internals**: Private execution mechanics hidden behind the seam.

### The Decision Test

Ask: **Can the defect be resolved completely behind the seam with zero seam changes, zero caller modifications, and zero downstream defensive workarounds?**

- **YES** $\rightarrow$ **`LOCAL`**: The seam is sound. The internal implementation failed its contract.
- **NO** $\rightarrow$ **`ARCHITECTURAL`**: The seam is inadequate.

### Seam Evaluation Levers

- **The Deletion Test**: If the internal implementation behind the seam is rewritten from scratch, callers remain completely unaffected. When a fix requires altering caller expectations, the fault is in the seam.
- **Ambient State Mutation**: Interfaces must return calculated results. Mutating shared or ambient caller state indicates an inadequate seam.
- **Temporal Coupling**: Requiring implicit execution ordering without enforcing it through the interface indicates an inadequate seam.

---

## 2. Process

1. **Gather Context**:
   - If full context and related code are already known, proceed directly.
   - Otherwise, read the relevant code and trace the seam using `grep_search` and `view_file` until the seam is understood.

2. **Evaluate & Classify**:
   - Contrast caller expectations with seam guarantees using the Decision Test and Evaluation Levers.
   - Group defects into `LOCAL` and `ARCHITECTURAL`.

3. **Output**:
   - Output the two groups with the affected seam, broken invariant, and structural rationale for each defect.
