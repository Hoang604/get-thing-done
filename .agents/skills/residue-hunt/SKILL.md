---
name: residue-hunt
description: Dispatch residue-hunter on a scope with a 5-minute budget, then collect its transition residue report
disable-model-invocation: true
---

## 1. Dispatch

Take the scope from the user's message: the paths they named, or `entire codebase` when they named none. Invoke `invoke_subagent` with:
- **TypeName**: `residue-hunter`
- **Role**: `Residue Hunter`
- **Prompt**: `Scope: <scope>. Parent conversation ID: <your conversation-id>.`

The prompt carries exactly these two values. The subagent already knows its job.

*Completion criterion*: the subagent is running and you hold its conversation ID.

## 2. Schedule the budget

In the same turn, call `schedule` with:
- **DurationSeconds**: `300`
- **TimerCondition**: `<subagent conversation ID>`
- **Prompt**: `Budget exhausted: send the graceful stop to residue-hunter <subagent conversation ID>.`

Then end your turn. If the subagent replies before the timer fires, the timer is cancelled. Skip to step 4.

## 3. Graceful stop

When the timer fires, call `send_message` to the subagent with exactly:

`STOP: Time budget exhausted. Stop reading now, finalize the report with the findings confirmed so far and the coverage list, deliver it, and reply with your completion line.`

Then end your turn and wait for the subagent's reply.

## 4. Present

When the subagent's completion line arrives, read `<appDataDir>/brain/<your conversation-id>/transition_residue_report.md` with `view_file`. Reply to the user with a link to it, its Status, and the LAZY and WEAK counts.

*Completion criterion*: the user holds a link to the delivered report and knows whether coverage was complete.
