---
name: residue-hunt
description: Dispatch residue-hunter on a scope with a 5-minute budget, then collect its transition residue report
disable-model-invocation: true
---

## 1. Dispatch

Take the scope from the user's message: the paths they named, or `entire codebase` when they named none. Invoke `Agent` with `run_in_background: true` and:
- **subagent_type**: `residue-hunter`
- **description**: `Residue Hunter`
- **prompt**: `Scope: <scope>. Parent conversation ID: ${CLAUDE_SESSION_ID}.`

The prompt carries exactly these two values. The subagent already knows its job.

*Completion criterion*: the subagent is running and you hold its agent ID.

## 2. Schedule the budget

In the same turn, call `Bash` with `sleep 300` and `run_in_background: true`.

Then end your turn. If the subagent replies before the timer fires, stop the timer with `TaskStop`. Skip to step 4.

## 3. Graceful stop

When the timer fires, call `SendMessage` to the subagent's agent ID with exactly:

`STOP: Time budget exhausted. Stop reading now, finalize the report with the findings confirmed so far and the coverage list, deliver it, and reply with your completion line.`

Then end your turn and wait for the subagent's reply.

## 4. Present

When the subagent's completion line arrives, read `~/.claude/gtd-brain/${CLAUDE_SESSION_ID}/transition_residue_report.md` with `Read`. Reply to the user with a link to it, its Status, and the LAZY and WEAK counts.

*Completion criterion*: the user holds a link to the delivered report and knows whether coverage was complete.
