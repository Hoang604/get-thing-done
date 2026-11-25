---
name: code-review
description: Coordinate parallel security and architecture-perf code-review subagents over a scope with a 10-minute budget, then merge into one unified report
disable-model-invocation: true
---

When merging findings, checking severity alignment, or formatting the delivered report, read `/home/hoang/.gemini/config/plugins/gtd-audit/skills/code-review/review-contract.md` to apply the canonical rubric and anchor format.

## 1. Resolve scope and dispatch

Take the review scope from the user's message:
- the target paths or modules they named;
- otherwise, uncommitted changes in the workspace;
- otherwise, the last commit;
- or `entire codebase` when asked for a repo audit.

In the same turn, invoke `invoke_subagent` in parallel for both reviewers:
1. **TypeName**: `security-reviewer`, **Role**: `Security Reviewer`, **Prompt**: `Scope: <scope>.`
2. **TypeName**: `architecture-perf-reviewer`, **Role**: `Architecture & Perf Reviewer`, **Prompt**: `Scope: <scope>.`

Each prompt carries only the scope. Each subagent already holds its full review protocol.

*Completion criterion*: both subagents are running and you hold both conversation IDs.

## 2. Schedule the budget

In the same turn (or immediately after receiving both conversation IDs), call `schedule` once per subagent so each timer cancels automatically if its subagent finishes early:
- **DurationSeconds**: `600`
- **TimerCondition**: `<security-reviewer conversation ID>`
- **Prompt**: `Budget exhausted: send the graceful stop to security-reviewer <security-reviewer conversation ID>.`
- **DurationSeconds**: `600`
- **TimerCondition**: `<architecture-perf-reviewer conversation ID>`
- **Prompt**: `Budget exhausted: send the graceful stop to architecture-perf-reviewer <architecture-perf-reviewer conversation ID>.`

Then end your turn and wait for both subagents' completion lines (or any timer wakeup).

## 3. Graceful stop

When a timer fires for a subagent that has not yet replied, call `send_message` to that subagent with exactly:

`STOP: Time budget exhausted. Stop reading now, finalize the report with the findings confirmed so far and the coverage list, deliver it, and reply with your completion line.`

Then end your turn and wait until both subagents have returned their completion lines before proceeding to Step 4.

## 4. Merge and deliver

Read both subagent reports in full. Before writing the unified report, emit a **Merge Disposition** covering every finding ID from both reports (`S-1..S-m` from `security-reviewer`, `A-1..A-n` from `architecture-perf-reviewer`) individually while holding all other findings fixed, assigning each exactly one outcome:

- **`MERGE -> #<k>`** (same code location and same causal flaw as another finding): collapse into one finding at the higher severity, preserving concrete triggers, consequences, and violated principles from both lenses under one smallest fix.
- **`KEEP -> #<k>`** (distinct causal flaw): retain as its own numbered finding so every trigger remains independently verifiable; add `cross-link #<j>` when a single boundary change resolves both this finding and a companion finding from the other lens.

In the same disposition, union `Open Questions` (deduplicating pairs turning on the same external rule or deployment assumption) and list every unread file or skipped runtime check tagged by which lens missed it (`security`, `architecture-perf`, or `both`).

Construct the merged report strictly from this disposition and write it to `<appDataDir>/brain/<conversation-id>/<report-name>.md` following the anchor format in `review-contract.md`, numbering findings sequentially (`1, 2, ...`) across severity groups so `/gtd-audit:verify-issue` can consume it directly. Write `Not checked: None (full scope read).` only when both subagents completed full coverage. Reply in chat with the clickable link to the merged report, counts per severity, and coverage status per lens.

*Completion criterion*: every input finding ID from both subagents appears in the Merge Disposition (zero silently dropped findings), every unread path names its missing lens, the merged report exists on disk matching the anchor format, and the chat reply provides its link, severity counts, and coverage status.
