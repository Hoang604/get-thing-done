---
name: audit-spec-alignment
description: Audit change against SPEC.md.
disable-model-invocation: true
---

# audit-spec-alignment

## Core Concepts (Leading Words)
- **Anchor**: A specific, unambiguous rule, logic, or requirement written in the spec.
- **Fog**: A section in the spec that is ambiguous, contradictory, or lacks implementation details.
- **Fabrication**: Logic, conditions, or features present in the code that have zero backing in the spec (rogue logic).

## Steps

### Step 1: Spec Extraction
Parse the spec document line by line into **Anchors** and **Fog**.
- **Completion Criterion**: Every single sentence and bullet point in the spec is categorized as either an Anchor or Fog. Zero skipped requirements.

### Step 2: Code Audit
Trace every **Anchor** across the target codebase using search and read tools (`grep_search`, `view_file`) to inspect all call sites and references. Categorize every logical block (functions, conditionals, state changes, UI components) mapped to those files:
- **Match**: Code implements the Anchor exactly as specified.
- **Deviation**: Code attempts to implement the Anchor but deviates, misses edge cases, or introduces defects.
- **Fabrication**: Code logic, checks, or features that exist with zero backing in the spec (unrequested scope or hallucinated logic).
- **Completion Criterion**: 100% of logical blocks across the target codebase files are explicitly mapped to an Anchor OR tagged as Fabrication. Verification must be proven by inspecting actual code implementations line-by-line, never assumed from function signatures, file basenames, or comments.

### Step 3: Synthesis & Reporting
Generate the final audit report strictly adhering to the `Audit Report Format` reference below, and save it as a new markdown artifact file inside the artifact directory (`<appDataDir>/brain/<conversation-id>/audit_alignment_report.md`).
- **Completion Criterion**: The audit report artifact file is successfully created in the artifact directory, strictly containing all 4 sections with zero untagged assumptions, using GitHub-style blockquote alerts for all deductions in Section 4.

---

## Reference: Audit Report Format

When executing Step 3, write the final output directly to a markdown artifact file using exactly these four headings:

### 1. Cleared Anchors
List all **Anchors** from the spec that the code correctly and perfectly implements.
- Format: `- **[Anchor Summary]** -> [file basename](file:///path/to/file#Lxx-Lyy)`

### 2. Broken Anchors
List all **Anchors** where the code deviates, implements them incorrectly, or misses them entirely.
- Format:
  `- **[Anchor Summary]** -> [file basename](file:///path/to/file#Lxx-Lyy)`
  `  - **Deviation**: [Exact mechanical explanation of the failure or deviation]`

### 3. Fabrications
List logic, extra checks, or features found in the code that have no corresponding **Anchor** in the spec.
- Format:
  `- **[Fabricated Feature/Logic]** -> [file basename](file:///path/to/file#Lxx-Lyy)`
  `  - **Rogue Scope**: [Explain exactly what the code is doing that the spec never requested]`

### 4. Fog & Deductions
List the **Fog** areas from the spec (ambiguous or missing details) and how the code currently handles them.
**CRITICAL RULE**: Any assumption, deduction, or hypothesis you make about what the spec *probably* meant MUST be formatted inside a GitHub-style alert (`> [!NOTE]` or `> [!WARNING]`). Never write deductions as plain narrative text.
- Format:
  `- **Fog**: "[Quote exact ambiguous spec passage]"`
  `  - **Current Code Execution**: [Exact mechanical state of how the code handles it right now]`
  `  > [!NOTE] Agent Deduction`
  > [Your explicit technical deduction about whether this implementation is right or wrong, and what the true spec intent might be.]