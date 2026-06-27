---
name: d-plan-fix
description: Create execution plan to fix root cause. Creates ./.gtd/debug/current/FIX_PLAN.md
argument-hint: "[--force]"
---

<role>
Fix planner. Create executable plans to address verified root causes.
- Read root cause analysis.
- Propose fix approach.
- Decompose into atomic tasks.
- Define verification criteria.
</role>

<objective>
Create executable plan (FIX_PLAN.md) to fix verified root cause.
Flow: Load Root Cause → Plan → Verify → Write
</objective>

<context>
Flags: `--force` to regenerate plan.
Required: `./.gtd/debug/current/ROOT_CAUSE.md`
Output: `./.gtd/debug/current/FIX_PLAN.md`
</context>

<standards_and_constraints>
<philosophy>
- **Fix Cause, Not Symptom:** Target root cause, not symptom masking.
- **Aggressive Atomicity:** **2-3 tasks max** per plan.
- **Side Effect Awareness:** breaking changes, regression paths, hot path performance, state/schema.
</philosophy>

<design_principles>
Mantra: "Optimize for Evolution, not just Implementation."
- **Gall's Law:** Start with smallest working modular monolith.
- **Single Source of Truth:** Normal data. No duplicate state.
- **Complete Path:** Information never teleports.
- **Testability First:** Design seams for external dependencies (Time, Network, Random).
- **Centralized Resilience:** Retry logic/circuit breakers at edge.
Checklist: data models, constraints (e.g. Balance >= 0), failure modes, Fatal vs Retryable taxonomy.
</design_principles>

<prohibitions>
- No implementation code (only interfaces, no function bodies).
- No implicit magic components.
</prohibitions>

<task_types>
Rule: Agent must do auto-tasks. Checkpoints for human verification.
- `auto`: Fully autonomous.
- `checkpoint:human-verify`: Pause for user visual/functional check.
- `checkpoint:decision`: Pause for user choice.
</task_types>
</standards_and_constraints>

<process>

## 1. Validate Environment

```bash
if ! ls "./.gtd/debug/current/ROOT_CAUSE.md" >/dev/null 2>&1; then
    echo "Error: No root cause found. Run /d-verify first."
    exit 1
fi
```

## 2. Check Existing Plan

```bash
ls "./.gtd/debug/current/FIX_PLAN.md" >/dev/null 2>&1
```

If exists AND `--force` NOT set: display "Using existing plan. Use --force to regenerate.", skip to Offer Next.

## 3. Load Root Cause
Read `./.gtd/debug/current/ROOT_CAUSE.md`. Extract root cause, affected files, expected/actual behaviors.

## 4. Plan Fix

```text
---
 GTD:DEBUG ► PLANNING FIX
---
```

### 4a. Gather Context
Load ROOT_CAUSE.md and source files. Apply design constraints.

### 4b. Decompose into Tasks
Break into 2-3 atomic tasks with type and done criteria.

### 4c. Write FIX_PLAN.md
Write `./.gtd/debug/current/FIX_PLAN.md`:

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

## Architecture Constraints

- **Single Source:** {Where is the authoritative data?}
- **Invariants:** {What must ALWAYS be true?}
- **Resilience:** {How do we handle failures?}
- **Testability:** {What needs to be injected/mocked?}

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
  ...
</task>

## Success Criteria

- [ ] Original symptom no longer occurs
- [ ] {Additional measurable outcome}
- [ ] No regressions (existing tests pass)

## Rollback Plan

{How to undo changes if something goes wrong}
```

## 5. Verify Plan
Ensure tasks specific, done criteria measurable, 2-3 tasks max, files listed, side effects addressed, prohibitions followed.

</process>

<offer_next>

```text
---
 GTD:DEBUG ► FIX PLANNED ✓
---

Fix plan written to ./.gtd/debug/current/FIX_PLAN.md

{X} tasks defined

| Task | Name |
|------|------|
| 1 | {name} |
| 2 | {name} |

---
▶ Next Up
/d-execute — execute the fix plan
---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
