---
name: unify
description: Merge a task spec into the global Product Specification.
argument-hint: "[task_name]"
---

<objective>
Update `./.gtd/PRODUCT.md` with changes from `./.gtd/<task_name>/SPEC.md`.
</objective>

<process>
1. Load `./.gtd/<task_name>/SPEC.md` (extract Ultimate Goal, Target Feature).
2. Load `./.gtd/PRODUCT.md`.
3. Map changes:
   - New features → append Feature Inventory.
   - Modified rules → update Domain Rules.
   - Deprecations → mark Deprecated.
   - Ultimate Goal → update Strategic Achievements / Product DNA.
4. Write `./.gtd/PRODUCT.md`.
</process>

<offer_next>

```text
---
 GTD ► PRODUCT SPEC UPDATED ✓
---

Source of Truth updated: ./.gtd/PRODUCT.md

Changes merged from: {task_name}

---
▶ Next Up
/archive {task_name} — archive the completed task
---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
