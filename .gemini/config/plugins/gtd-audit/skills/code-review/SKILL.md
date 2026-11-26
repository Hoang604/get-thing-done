---
name: code-review
description: Coordinate parallel security and architecture-perf code-review subagent pairs over a sized scope with a 10-minute budget, then index and reconcile into one main report
disable-model-invocation: true
---

**When** merging findings, checking severity or class alignment, or formatting the delivered report, read `review-contract.md` to apply the canonical rubric and anchor format.

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

## 4. Reconcile, index, and deliver

Read all `2K` subagent reports in full. Before writing the main report, emit a **Merge Disposition** covering every finding ID across all reports (`S-1..S-m` and `A-1..A-n`, prefixed by slice `S<k>-...` / `A<k>-...` when `K > 1`) individually while holding all other findings fixed, assigning each exactly one outcome:

- **`MERGE -> #<k>`** (same code location and same causal flaw as another finding): write one unified finding in the main report at the higher severity and higher class (`ARCHITECTURAL` over `LOCAL`), preserving concrete triggers, consequences, and violated principles under one smallest fix (at the originating Layer 3 boundary when `ARCHITECTURAL`).
- **`KEEP -> #<k>`** (distinct causal flaw): leave the full finding write-up solely in its subagent report (never copy its body into the main report); index it in `#### Findings Index` with a clickable link directly to its exact `#L<start>-L<end>` lines in that subagent report, adding `cross-link #<j>` in the index when a single boundary change resolves both this finding and a companion finding.
- **`CONFLICT -> #<k>`** (two findings propose mutually incompatible fixes on the same code): verify against the repository whether one unified fix satisfies both invariants simultaneously; if yes, write one unified finding in the main report at the higher severity and higher class with that fix; otherwise, if severities differ write the higher-severity finding in the main report and add an `Open Question` presenting both trade-offs, and if severities are equal move both competing proposals into an `Open Question` in the main report for the user to choose.

In the same disposition, union `Open Questions` (deduplicating pairs turning on the same external rule or deployment assumption), list every unread file or skipped runtime check tagged by missing lens (`security`, `architecture-perf`, or `both`), and check whether distinct `KEEP` findings across lenses or slices combine into a higher-severity exploit or failure chain (writing any confirmed chain in `#### Merged & Reconciled Findings`).

Write the main report to `<appDataDir>/brain/<conversation-id>/<report-name>.md` following the **Coordinator Main Report Anchor** in `review-contract.md`, ordering `#### Findings Index` by severity (`Critical` → `Major` → `Minor`) with sequential numbers (`1, 2, ...`). Then eliminate stale entries in any affected subagent report via `edit_file`:
- Replace each `MERGE` or `CONFLICT` finding's body in its subagent report with a single pointer line (`> **<ID>** — Superseded by [#<k>](file://<main-report-path>) (\`MERGE\` | \`CONFLICT\`).`, or pointing to `Open Questions` when equal-severity `CONFLICT` moved both there).
- Replace any subagent report's `#### Open Questions` entries with a single pointer line (`Consolidated into [<report-name>.md](file://<main-report-path>).`) so `Open Questions` live canonically in the main report.
- Ensure every `KEEP` link in `#### Findings Index` points to the exact post-edit `#L<start>-L<end>` lines of its subagent report.

Write `Not checked: None (full scope read).` only when every subagent across all slices completed full coverage. Reply in chat with the clickable link to the main report, counts per severity and `LOCAL`/`ARCHITECTURAL` class, and coverage status per lens.

*Completion criterion*: every input finding ID from all `2K` subagent reports appears in the Merge Disposition (zero silently dropped findings), every `KEEP` finding stays in its subagent report with an accurate post-edit `#L<start>-L<end>` link in `#### Findings Index`, every `MERGE`/`CONFLICT` finding and consolidated `Open Question` is replaced by a pointer in its subagent report (zero stale bodies left on disk), every unread path names its missing lens, the main report matches the Coordinator anchor format, and the chat reply provides its link, severity and class counts, and coverage status.
