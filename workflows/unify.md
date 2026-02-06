---
name: unify
description: Merge a task spec into the global Product Specification.
argument-hint: "[task_name]"
---

<objective>
Update ./.gtd/PRODUCT.md to reflect the changes delivered by ./.gtd/<task_name>/SPEC.md.
</objective>

<process>
1. Load ./.gtd/<task_name>/SPEC.md (The Change).
   - Extract Ultimate Goal
   - Extract Target Feature
2. Load ./.gtd/PRODUCT.md (The Current State).
3. Identify:
   - New features added? -> Append to Feature Inventory.
   - Business rules modified? -> Update Domain Rules.
   - Features deprecated? -> Mark as Deprecated/Removed.
   - **Ultimate Goal achieved?** -> Add to "Strategic Achievements" or "Product DNA" section.
4. Update ./.gtd/PRODUCT.md.
</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PRODUCT SPEC UPDATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Source of Truth updated: ./.gtd/PRODUCT.md

Changes merged from: {task_name}

─────────────────────────────────────────────────────
▶ Next Up
/archive {task_name} — archive the completed task
─────────────────────────────────────────────────────
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
