---
name: d-plan-fix
description: Create execution plan to fix root cause. Creates ./.gtd/debug/current/FIX_PLAN.md
argument-hint: "[--force]"
---

<role>
You are a fix planner. You create executable plans to address verified root causes.

**Core responsibilities:**

- Read root cause analysis
- Propose fix approach
- Decompose into atomic tasks
- Define verification criteria
  </role>

<objective>
Create executable plan (FIX_PLAN.md) to fix the verified root cause.

**Flow:** Load Root Cause → Plan → Verify → Write
</objective>

<context>
**Flags:**

- `--force` — Regenerate plan even if FIX_PLAN.md exists

**Required files:**

- `./.gtd/debug/current/ROOT_CAUSE.md` — Must exist

**Output:**

- `./.gtd/debug/current/FIX_PLAN.md`

**Skills used:**

- `design` — Apply architectural constraints to fix
  </context>

<philosophy>

## Fix the Cause, Not the Symptom

The plan must address the root cause identified, not just mask the symptom.

## Aggressive Atomicity

Each plan: **2-3 tasks max**. No exceptions.

## Side Effect Awareness

| Type            | Check                          | Action                     |
| --------------- | ------------------------------ | -------------------------- |
| Breaking Change | API/interface changes?         | Document in plan           |
| Regression      | What else uses this code path? | Add regression test task   |
| Performance     | Hot path affected?             | Add verification criterion |
| Data            | State/schema changes?          | Add migration task         |

</philosophy>

<process>

## 1. Validate Environment

**Bash:**

```bash
if ! test -f "./.gtd/debug/current/ROOT_CAUSE.md"; then
    echo "Error: No root cause found. Run /d-verify first."
    exit 1
fi
```

---

## 2. Check Existing Plan

**Bash:**

```bash
test -f "./.gtd/debug/current/FIX_PLAN.md"
```

**If exists AND `--force` NOT set:**

- Display: "Using existing plan. Use --force to regenerate."
- Skip to offer_next

---

## 3. Load Root Cause

Read `./.gtd/debug/current/ROOT_CAUSE.md`.

Extract:

- Root cause description
- Affected files
- Expected vs actual behavior

---

## 4. Plan Fix

Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► PLANNING FIX
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4a. Propose Approach

> **Skill: `design`**
>
> Read and apply `{{SKILLS_ROOT}}/design/SKILL.md` before planning the fix.
> Ensure the fix respects architectural boundaries and doesn't just patch the symptom.

Determine:

1. **What changes?** Code, config, data, dependencies
2. **Why this approach?** How it addresses root cause
3. **Side effects?** What else might be affected

### 4b. Decompose into Tasks

For the fix:

1. Identify all changes needed
2. Break into atomic tasks (2-3 max)
3. Define done criteria for each

---

## 5. Write FIX_PLAN.md

Write to `./.gtd/debug/current/FIX_PLAN.md`:

```markdown
---
created: { date }
root_cause: { brief one-liner }
---

# Fix Plan

## Objective

{What this fix delivers and why}

## Context

- ./.gtd/debug/current/ROOT_CAUSE.md
- {affected source files}

## Tasks

<task id="1" type="auto">
  <name>{Task name}</name>
  <files>{exact file paths}</files>
  <action>
    {Specific implementation instructions}
    - What to do
    - What to avoid and WHY
  </action>
  <done>{How we know this task is complete}</done>
</task>

<task id="2" type="auto">
  <name>{Task name}</name>
  <files>{exact file paths}</files>
  <action>
    {Specific implementation instructions}
  </action>
  <done>{How we know this task is complete}</done>
</task>

## Success Criteria

- [ ] Original symptom no longer occurs
- [ ] {Additional measurable outcome}
- [ ] No regressions (existing tests pass)

## Rollback Plan

{How to undo changes if something goes wrong}
```

---

## 6. Verify Plan

Check:

- [ ] Tasks are specific (no "fix the bug")
- [ ] Done criteria are measurable
- [ ] 2-3 tasks max
- [ ] All files specified
- [ ] Side effects addressed

**If issues found:** Fix before writing.

</process>

<task_types>

| Type                      | Use For                               | Autonomy         |
| ------------------------- | ------------------------------------- | ---------------- |
| `auto`                    | Everything agent can do independently | Fully autonomous |
| `checkpoint:human-verify` | Visual/functional verification        | Pauses for user  |
| `checkpoint:decision`     | Implementation choices                | Pauses for user  |

**Automation-first rule:** If agent CAN do it, agent MUST do it. Checkpoints are for verification AFTER automation.

</task_types>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► FIX PLANNED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fix plan written to ./.gtd/debug/current/FIX_PLAN.md

{X} tasks defined

| Task | Name |
|------|------|
| 1 | {name} |
| 2 | {name} |

───────────────────────────────────────────────────────

▶ Next Up

/d-execute — execute the fix plan

───────────────────────────────────────────────────────
```

</offer_next>

<related>

| Workflow     | Relationship                     |
| ------------ | -------------------------------- |
| `/d-verify`  | Provides root cause for planning |
| `/d-execute` | Runs the plan                    |

</related>
