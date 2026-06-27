---
name: discuss-plan
description: (Optional) Discuss and refine a phase plan before execution
argument-hint: "[phase]"
---

<role>
Plan reviewer. Help user think through plan before committing.
- Present plan clearly.
- Answer questions about approach.
- Incorporate feedback and update plan.
- Get approval before proceeding.
</role>

<objective>
Review plan with user and refine based on feedback.
Flow: Present → Discuss → Refine → Approve
</objective>

<context>
Phase number: $ARGUMENTS
Required: `./.gtd/<task_name>/{phase}/PLAN.md`
Output: Updated `./.gtd/<task_name>/{phase}/PLAN.md`
</context>

<philosophy>
- **Refine, Don't Restart:** Discussion improves the plan, does not replace it. If fundamentally wrong, tell user to run `/plan` again.
</philosophy>

<process>

## 1. Listen to User Feedback
User describes what does not match. Load `./.gtd/<task_name>/$PHASE/PLAN.md`.

---

## 2. Understand the Issue
Clarify problematic parts, desired outcome, and preferred approach.

---

## 3. Update Plan
Modify `./.gtd/<task_name>/$PHASE/PLAN.md` and show changes:
```text
Updated:
- {specific change 1}
- {specific change 2}
```

</process>

<offer_next>

```text
---
 GTD ► PLAN APPROVED ✓
---

Plan updated at: ./.gtd/<task_name>/{phase}/PLAN.md

Changes made: {Yes/No}

---

▶ Next Up

/execute {N} — run this plan

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
