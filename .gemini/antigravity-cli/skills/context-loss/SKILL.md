---
name: context-loss
description: You must read this skill immediately via view_file whenever context compaction occurs before calling any other tool or executing any task, unless the user's message prior to compaction explicitly instructed what to do upon compaction.
---

# Context Loss Recovery Protocol

This skill is activated immediately when context has been compacted or previous context is lost.

## Strict Prohibitions

1. **Transcript Inspection Prohibition**: NEVER access conversation transcripts or logs (`transcript.jsonl`, `transcript_full.jsonl`) under any circumstances unless the user explicitly asks for it.
2. **Git Command Prohibition**: NEVER run any `git` command unless the user explicitly asks for it.

## Bypass Condition

You may bypass reading and executing this skill if and only if the user's message prior to compaction explicitly specified what actions to take when context compaction occurs. In that case, follow the user's explicit instructions directly.

---

## Recovery Workflow

Assess execution state from `<summary>` and inspect the most recent visible `# User Request` in full detail.

### Case 1: Guided Execution (A File on Disk Defines the Task's Steps or Deliverables)

When executing a task governed by a guiding document on disk:

1. **Read Uncompleted Plan Slice & Working Set**:
   - Call `view_file` in one batch on the uncompleted `StartLine`–`EndLine` slice of the guiding document and every file or `file:start-end` slice listed in `<summary>`'s **Read-next working set** (or, when `<summary>` omits the working set, the `#L<start>-L<end>` slices the guiding document references for the first uncompleted step).
   - When the guiding document is an implementation plan, include the `execute` skill in the same `view_file` batch.
2. **Continue Execution**:
   - Taking `<summary>` as the record of completed work, execute from the first uncompleted step immediately and deliver the completion report in the format required by the guiding document (or `execute` skill).

---

### Case 2: Unguided Execution (No Guiding Document on Disk)

When no file on disk defines the task's steps:

1. **Echo Request**: Output the verbatim text of the user's most recent visible `# User Request`.
2. **Report Status**: State what has been completed and what remains unfinished based on `<summary>`.
3. **Continue**: When unfinished work remains, call `view_file` in one batch on every file or `file:start-end` slice in `<summary>`'s **Read-next working set** and continue the work right after the report. When nothing remains, end with the report.
