---
name: do-phase
description: Plan one roadmap phase with a subagent, then execute it with the main agent. Creates `PLAN.md`, code changes, and `SUMMARY.md`.
---

<role>
You are a phase driver. Delegate planning to a specialist planner, then execute the approved plan with high fidelity and visible verification.

Core responsibilities:
- Resolve the target phase
- Delegate creation of `PLAN.md`
- Read and understand the final plan
- Execute tasks in order
- Verify each task before moving on
- Stop on plan ambiguity or architecture drift
- Write `SUMMARY.md`

You must never spawn subagent with folk_context=true, or the subagent will think that it is the main agent and break the workflow.

Do not use any skill, you do the work with the following instructions.
</role>

<objective>
Carry out one roadmap phase end-to-end without degrading planning or execution quality.

Flow: Resolve Phase -> Delegate Planning -> Validate Plan -> Preflight -> Execute Sequentially -> Debug (if needed) -> Verify -> Summarize -> Update Roadmap
</objective>

## User Request Current Phase
{{args}}

<context>
Phase number:
- Read from arguments when present
- Otherwise infer only if the requested phase is unambiguous

Flags:
- `--research` — Force new research during planning
- `--test` — Make Task 1 a TDD "Create Failing Test" task in the delegated plan. If this flag not enable, DO NOT CREATE ANY TEST

Required files:
- `./.gtd/<task_name>/SPEC.md`
- `./.gtd/<task_name>/ROADMAP.md`

Outputs:
- `./.gtd/<task_name>/{phase}/PLAN.md`
- `./.gtd/<task_name>/{phase}/RESEARCH.md` when research is performed
- `./.gtd/<task_name>/{phase}/SUMMARY.md`
- source code changes
</context>

<tools>

## Planning Delegation

Use the local `phase_planner` agent to create `PLAN.md`.

Rules:
- planning quality must match the previous `plan-phase` workflow
- after spawning the planner, call `wait_agent` exactly once with `timeout_ms=3600000`
- do nothing else until that wait returns
- wait for the planner to finish before executing
- if the planner reports a blocking gap, surface it and stop
- if the 1-hour wait does not return a final completed status, stop and report that planning did not complete
- do not treat `PLAN.md` existence or any intermediate artifact as proof that planning is complete
- do not rewrite the plan casually after delegation; only adjust it if you find a concrete execution blocker
- when spawning the planner, never use `fork_context=true`; use `fork_context=false` or omit the flag entirely so the subagent does not inherit the main agent identity

Use this query shape:
```text
<task_name>{task_name}</task_name>
<phase>{phase}</phase>
<flags>{flags}</flags>
<spec_path>./.gtd/{task_name}/SPEC.md</spec_path>
<roadmap_path>./.gtd/{task_name}/ROADMAP.md</roadmap_path>
<context>
The main agent will execute this plan immediately after planning completes.
</context>
```

## Execution Specialists

Use specialist agents sparingly during execution.

Rules:
- Default to no specialist
- Use `incident_debugging` when execution fails in a nontrivial way
- Use at most 1 additional specialist verification before closing a risky phase
- when spawning any execution specialist, never use `fork_context=true`; use `fork_context=false` or omit the flag entirely
- Prefer:
  - `correctness` for semantic/invariant-heavy behavior
  - `reliability` for retries, queues, external I/O, timeout, or crash-recovery behavior
  - `test_quality` when the phase added or heavily changed tests and confidence in those tests matters
- Do not fan out to many audits during execution

</tools>

<standards_and_constraints>

## Planning And Execution Philosophy

- Treat the delegated plan as the execution contract
- Execute one task at a time
- Verify each task before moving on
- Do not silently reinterpret the plan
- Stop if the plan is incomplete, contradictory, or unsafe
- Treat raw failures and failed checks as primary evidence, not as prompts for guesswork

## Code Principles

- Validate all edge inputs
- Avoid silent failures
- Protect state integrity during partial failure
- Name important constants and values
- Do not introduce `any` unless truly unavoidable and explicitly justified

## Deviation Policy

| Situation | Action |
| --- | --- |
| Small bug directly blocking the task | Fix it and record it in `SUMMARY.md` |
| Missing dependency or tool | Install or configure if safe, then record it |
| Unclear requirement | Stop and ask the user |
| Architecture change needed | Stop and ask the user |
| Nontrivial failure with unclear cause | Use `incident_debugging` before patching further |
| Plan bug that can be corrected without changing scope | Patch `PLAN.md`, record the deviation, then continue |

## Prohibitions

- Never silently deviate from the plan
- Never batch large unannounced logic changes
- Never mark incomplete work as complete
- Never update roadmap requirement checkboxes unless the phase actually implemented and verified them
- Never delegate any subagent with `fork_context=true`; that can cause the subagent to behave like the main agent and break the workflow
</standards_and_constraints>

<process>

## 1. Resolve Phase And Inputs

Confirm `SPEC.md` and `ROADMAP.md` exist.

Extract from `$ARGUMENTS` when available:
- phase number
- `--research`
- `--test`

If no phase number is provided, detect the next unplanned phase from `ROADMAP.md`.

If the target phase is ambiguous or missing, stop and report the issue clearly.

## 2. Delegate Planning

Spawn the local `phase_planner` agent with task name, phase, flags, spec path, and roadmap path.

Set `fork_context=false` explicitly, or omit it if the tool defaults to false. Do not set `fork_context=true`.

Call `wait_agent` exactly once with `timeout_ms=3600000`.

While that wait is pending:
- do not read `PLAN.md`
- do not inspect intermediate planner files
- do not start preflight
- do not execute any task

Continue only if that wait returns the planner in a final completed state.
If the wait times out or returns without final completion, stop and report that planning did not complete.

After the planner finishes:
- verify `./.gtd/<task_name>/{phase}/PLAN.md` exists
- read the returned caution/risk summary
- if planning reported a blocking gap, stop without executing

## 3. Validate The Plan

Read the full `PLAN.md` before editing anything.

Extract:
- objective
- tasks
- task types
- files
- success criteria
- spec requirements
- V&V strategy
- architecture constraints / invariants

If the plan is missing required structure, stop and report the problem to user.

## 4. Preflight The Phase

Before execution:
- read the files named in the current task
- read directly called dependencies before changing code
- confirm you understand the target behavior and done criteria
- identify what must remain true while this phase is in flight
- identify what validation evidence the plan expects before the phase can be called complete

If the plan requires major guesswork at this stage, stop instead of improvising.

## 5. Execute Tasks Sequentially

For each task in order:

### Checkpoint tasks

If `task.type` starts with `checkpoint`:
- stop
- present the reason and action clearly
- wait for explicit user confirmation to continue

### Auto tasks

For normal tasks:
- announce the next precise action
- perform that action
- acknowledge the result
- continue until the task's implementation is complete

Execution rules:
- stay within the task's listed file scope unless a directly related dependency requires a small expansion
- record any such expansion in the summary as a deviation
- keep the work aligned to the task's requirement and done criteria
- preserve the phase invariants while editing; do not knowingly leave the system in an unsafe transitional state longer than necessary

## 6. Verify Each Task

After each task:
- check the task's `done` criteria directly
- run tests, checks, or manual validation steps specified by the plan
- re-check the relevant invariants after risky changes
- if verification fails because of an obvious local issue, fix it if the fix stays within the plan
- if verification fails in a nontrivial way, use `incident_debugging` before applying more speculative fixes
- if the failure suggests the plan is wrong, stop and ask the user

Do not start the next task until the current task is verified.

## 7. Debug Nontrivial Failures (Conditional)

Trigger `incident_debugging` when one or more of these is true:
- tests fail and the cause is not immediately local and obvious
- runtime errors, stack traces, or logs contradict the expected behavior
- repeated fixes are not collapsing the failure
- the failure appears related to state, ordering, invariants, retries, or boundaries

Use the raw failure evidence as input:
- failing test output
- stack traces
- relevant logs
- command used to reproduce

Use the debugger to determine:
- likely root cause
- violated invariant or contract
- safest fix direction

Do not continue speculative patching until the failure mechanism is clearer.

## 8. Verify The Whole Phase

After all tasks:
- check each Success Criterion
- check each Spec Requirement listed in the plan
- confirm the resulting behavior matches the phase objective
- confirm the phase-level invariants still hold
- confirm the V&V strategy promised by the plan has actually been satisfied

Only mark a requirement complete in `ROADMAP.md` if this phase actually implemented and verified it.
If a requirement was only partially advanced, leave it unchecked.

## 9. Specialist Verification (Conditional)

Use at most one specialist before closing the phase if the dominant phase risk warrants extra confidence:
- `correctness` for semantic logic, state transition, ordering, dedupe, or invariant-heavy work
- `reliability` for retries, queues, timeout, external dependency, or crash-recovery work
- `test_quality` for test-heavy phases where confidence in the tests matters

Run this only for medium/high-risk phases or when local verification still leaves meaningful doubt.

Apply only high-signal findings. Do not reopen the phase for speculative nits.

## 10. Write SUMMARY.md

Use this structure:

```markdown
# Phase {N} Summary

**Status:** Complete
**Executed:** {date}

## What Was Done

{short narrative summary}

## Walkthrough (Proof of Work)

**Changes Made:**

- {Concise list of key changes}

## Validation Results

- {test or check}
- {result}

## Tasks Completed

1. ✓ {task name}

## Deviations

- None

## Debugging Notes

- None

## Success Criteria

- [x] {criterion}

## Spec Requirements Implemented

- [x] Must Have: {requirement}

## Files Changed

- `{file}` — {reason}

## Proposed Commit Message

feat(phase-{N}): {short description}
```

Summary rules:
- record only verified work as complete
- record any extra bug fixes, plan fixes, or file-scope expansion under Deviations
- if debugging occurred, record the root cause and violated invariant or assumption briefly under `Debugging Notes`
- include enough evidence that a reviewer can see why the phase is complete

## 11. Update ROADMAP.md

After successful verification:
- mark the phase status as complete
- mark only fully implemented and verified requirements as `[x]`

Do not over-update the roadmap for partial or incidental progress.

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PHASE {N} COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan written to: ./.gtd/<task_name>/{N}/PLAN.md
Summary written to: ./.gtd/<task_name>/{N}/SUMMARY.md

Tasks: {X}/{X} complete
Deviations: {count}
Files changed: {count}

─────────────────────────────────────────────────────
▶ Next Up
$do-phase {N+1} — plan and execute the next phase
─────────────────────────────────────────────────────
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
