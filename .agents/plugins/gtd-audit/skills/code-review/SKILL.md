---
name: code-review
description: Coordinate parallel security and architecture-perf code-review subagent pairs over a sized scope with a 10-minute budget, then merge into one unified report
disable-model-invocation: true
---

**When** merging findings, checking severity alignment, or formatting the delivered report, read `review-contract.md` to apply the canonical rubric and anchor format.

## 1. Resolve scope, size, shard, and dispatch

Take the review scope from the user's message:
- the target paths or modules they named;
- otherwise, uncommitted changes in the workspace;
- otherwise, the last commit;
- or `entire codebase` when asked for a repo audit.

Measure total target source and configuration bytes in one shell command (`wc -c`, excluding binaries, lockfiles, and build outputs; for diff scopes, measure the full size of each touched target file):
- **When** total target size is `<= 500 KB`: keep the scope as **1 slice** (`K = 1`).
- **When** total target size is `> 500 KB`: partition the target files along cohesive directory or subsystem boundaries into `K = min(4, ceil(total_bytes / 500 KB))` non-overlapping slices so each slice stays cohesive.

In one turn, invoke `invoke_subagent` in parallel for all `K` pairs (`2K` subagents total), passing this skill directory's `review-contract.md` path in `Contract:` and using the exact prompt structure below so the context-budget guard activates:
1. **TypeName**: `security-reviewer`, **Role**: `Security Reviewer` (or `Security Reviewer <k>` when `K > 1`), **Prompt**: `Review security scope: <scope-or-slice>. Contract: <skill-dir>/review-contract.md. Execute your blind security review protocol and deliver security_review_report.md.`
2. **TypeName**: `architecture-perf-reviewer`, **Role**: `Architecture & Perf Reviewer` (or `Architecture & Perf Reviewer <k>` when `K > 1`), **Prompt**: `Review architecture-perf scope: <scope-or-slice>. Contract: <skill-dir>/review-contract.md. Execute your blind architecture-perf review protocol and deliver architecture_perf_review_report.md.`

*Invocation Contract:* Dispatch with this exact prompt structure. Do NOT append custom conversational steering.

*Completion criterion*: target size is measured, `K` non-overlapping slices are assigned, all `2K` subagents are running, and you hold every conversation ID.

## 2. Schedule the budget

Immediately after receiving all conversation IDs, call `schedule` once per subagent in one turn so each timer cancels automatically if its subagent finishes early (use `DurationSeconds: 600` unless the user specified a different budget):
- **DurationSeconds**: `600`
- **TimerCondition**: `<subagent conversation ID>`
- **Prompt**: `Budget exhausted: send the graceful stop to <subagent role> <subagent conversation ID>.`

Then end your turn and wait for subagent completion lines or any timer wakeup.

*Completion criterion*: every running subagent has a matching timer scheduled with its `TimerCondition` set to its conversation ID, and the turn ends to wait for notifications.

## 3. Graceful stop

**When** a timer fires for a subagent that has not yet replied, call `send_message` to that subagent with exactly:

`STOP: Time budget exhausted. Stop reading now, finalize the report with the findings confirmed so far and the coverage list, deliver it, and reply with your completion line.`

Never kill a subagent after sending `STOP:`. End your turn and let it finish finalizing and return its completion line; only if a runtime notification reports that a subagent terminated with an unexpected failure without a completion line, read whatever partial report exists on disk (or record that slice and lens under `Not checked`) before continuing to Step 4.

*Completion criterion*: every timed-out subagent has received the exact `STOP:` message, and every subagent has either returned its completion line or terminated with failure.

## 4. Merge and deliver

Read all `2K` subagent reports in full. Before writing the unified report, emit a **Merge Disposition** covering every finding ID across all reports (`S-1..S-m` and `A-1..A-n`, prefixed by slice `S<k>-...` / `A<k>-...` when `K > 1`) individually while holding all other findings fixed, assigning each exactly one outcome:

- **`MERGE -> #<k>`** (same code location and same causal flaw as another finding): collapse into one finding at the higher severity, preserving concrete triggers, consequences, and violated principles from both lenses under one smallest fix.
- **`KEEP -> #<k>`** (distinct causal flaw): retain as its own numbered finding so every trigger remains independently verifiable; add `cross-link #<j>` when a single boundary change resolves both this finding and a companion finding from another report.
- **`CONFLICT -> #<k>`** (two findings propose mutually incompatible fixes on the same code): verify against the repository whether one unified fix satisfies both invariants simultaneously; if yes, collapse into one finding at the higher severity with that unified fix; otherwise, if severities differ retain the higher-severity finding and add an `Open Question` presenting both trade-offs, and if severities are equal move both competing proposals into an `Open Question` for the user to choose.

In the same disposition, union `Open Questions` (deduplicating pairs turning on the same external rule or deployment assumption) and list every unread file or skipped runtime check tagged by which lens missed it (`security`, `architecture-perf`, or `both`). After assigning dispositions, check whether distinct `KEEP` findings across lenses or slices combine into a higher-severity exploit or failure chain, noting any confirmed chain in the merged report.

Construct the merged report strictly from this disposition and write it to `<appDataDir>/brain/<conversation-id>/<report-name>.md` following the anchor format in `review-contract.md`, numbering findings sequentially (`1, 2, ...`) across severity groups so `/gtd-audit:verify-issue` can consume it directly. Write `Not checked: None (full scope read).` only when every subagent across all slices completed full coverage. Reply in chat with the clickable link to the merged report, counts per severity, and coverage status per lens.

*Completion criterion*: every input finding ID from all `2K` subagent reports appears in the Merge Disposition (zero silently dropped findings), every unread path names its missing lens, the merged report exists on disk matching the anchor format, and the chat reply provides its link, severity counts, and coverage status.
