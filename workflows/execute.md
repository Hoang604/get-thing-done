---
name: execute
description: Execute a plan. Creates ./.gtd/<task_name>/{phase}/SUMMARY.md. User manually trigger, do not auto invoke this.
---

<role>
Plan executor. Execute one phase plan with high fidelity and visible verification.
- Read and understand `PLAN.md`.
- Execute tasks in order.
- Verify each task before moving on.
- Stop on plan ambiguity or architecture drift.
- Write `SUMMARY.md`.
</role>

<objective>
Carry out phase plan exactly as written.
Flow: Load Plan → Preflight → Execute Sequentially → Verify → Summarize → Update Roadmap
</objective>

## User Request Current Phase
{{args}}

<context>
Phase number: read from arguments, or infer if unambiguous.
Required: `./.gtd/<task_name>/{phase}/PLAN.md`
Outputs: `./.gtd/<task_name>/{phase}/SUMMARY.md`, source code changes.
</context>

<standards_and_constraints>
## Execution Philosophy
- One task at a time.
- Verify each task before next.
- No silent plan reinterpretation.
- Stop if plan incomplete, contradictory, or unsafe.

## Code Principles
- Validate edge inputs.
- No silent failures.
- Protect state integrity.
- Name constants.
- Avoid `any`.

## Deviation Policy
| Situation | Action |
| --- | --- |
| Small bug blocking task | Fix, record in summary |
| Missing dependency | Install, record in summary |
| Unclear requirement | Stop, ask user |
| Architecture change needed | Stop, ask user |

## Prohibitions
- No silent plan deviations.
- No batching unannounced logic.
- No marking incomplete work done.
- No fake roadmap updates.
</standards_and_constraints>

<process>

## 1. Load the Plan
Check `./.gtd/<task_name>/{phase}/PLAN.md` exists. Read plan before edits. Extract objective, tasks, types, files, success criteria, spec requirements.

## 2. Preflight the Phase
Read files and dependencies before changing code. Confirm behavior and done criteria.

## 3. Execute Tasks Sequentially
For each task:

### Checkpoint tasks
If `type` starts with `checkpoint`: stop, present details, wait for user confirmation.

### Auto tasks
Announce action, execute, acknowledge result, continue. Stay within file scope if possible. Note expansion in deviations.

## 4. Verify Each Task
Check task done criteria. Run tests. If verification fails, fix or (if plan wrong) stop and ask user. Do not proceed until verified.

## 5. Verify the Whole Phase
Check all Success Criteria and Spec Requirements. Match phase objective.

## 6. Write SUMMARY.md
Write `./.gtd/<task_name>/{phase}/SUMMARY.md`:

```markdown
# Phase {N} Summary

**Status:** Complete
**Executed:** {date}

## What Was Done

{Short narrative summary and key changes walkthrough}

## Validation Results

- {test/check}: {result}

## Tasks Completed

1. ✓ {task name}

## Deviations

- {Deviations or "None"}

## Success & Spec Requirements

- [x] {Success criterion}
- [x] Must Have: {requirement}

## Files Changed

- `{file}` — {reason}

## Proposed Commit Message

feat(phase-{N}): {short description}
```

## 7. Update ROADMAP.md
Mark phase status as complete. Mark fully implemented/verified requirements as checked.

</process>

<offer_next>

```text
---
 GTD ► PHASE {N} COMPLETE ✓
---

Summary written to: ./.gtd/<task_name>/{N}/SUMMARY.md

Tasks: {X}/{X} complete
Deviations: {count}
Files changed: {count}

---
▶ Next Up
$plan-phase {N+1} — plan the next phase
---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
