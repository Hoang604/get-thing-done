---
name: verify-issue
description: trace codebase to verify if issues flagged in code review are false positives.
disable-model-invocation: true
---
Execute issue verification strictly following this instruction set.

**PHASE 1: TRACE**
1. Extract the "Actionable Issues & Bottlenecks" from the most recent code-review report in the conversation.
2. Search the global codebase for mitigation patterns related to the extracted issues (e.g., background workers, global state managers, eviction policies, lifecycle hooks).
3. Read the suspected mitigation files.

**PHASE 2: VERDICT & REPORTING**
Evaluate if the discovered external code nullifies the flagged local issues.
Output a strict verification report using this exact format:

**1. Mitigation Search Scope**
List the exact files searched and read.

**2. Verdicts**
For each issue extracted, provide the verdict:
*   `[Original Issue Title]`
    *   **Verdict:** [True Positive OR False Positive]
    *   **Mitigation Found:** [Name the specific pattern/code block that mitigates the issue, or "None"]
    *   **Explanation:** [Briefly explain how the external code handles the problem, or why it remains a valid issue]

**CONSTRAINTS**
*   Do not modify code.
*   Do not guess or invent business rules.
*   Keep the report direct and concise. Omit conversational filler.
