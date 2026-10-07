---
name: context-loss
description: You must read this skill immediately via view_file whenever context compaction occurs before calling any other tool or executing any task, unless the user's message prior to compaction explicitly instructed what to do upon compaction.
---

# Context Loss Recovery Protocol

This skill is activated immediately when context has been compacted or previous context is lost.

## Strict Prohibitions

1. **Transcript Inspection Prohibition**: NEVER run any command or tool to inspect, search, or read `transcript.jsonl`, `transcript_full.jsonl`, or conversation logs under any circumstances unless the user explicitly asks for it.
2. **Git Command Prohibition**: NEVER run any `git` command (`git status`, `git diff`, `git log`, etc.) unless the user explicitly asks for it.

## Bypass Condition

You may bypass reading and executing this skill if and only if the user's message prior to compaction explicitly specified what actions to take when context compaction occurs. In that case, follow the user's explicit instructions directly.

---

## Recovery Workflow

Assess execution state and inspect the most recent visible user request in full detail (not compacted).

### Case 1: Currently in Execution (Guided Task / Plan)

If currently in the middle of executing a task guided by an instruction file, audit report, or implementation plan:

1. **Read Guiding Document**:
   - Locate and read the file currently guiding the execution (e.g., `implementation_plan.md`, audit report, task spec, checklist, or instruction file in workspace/artifacts) completely in full without line limits using `view_file` (must read all lines from beginning to end; if the file exceeds 800 lines, page through with `StartLine`/`EndLine` until completely read).
   - Read all referenced files or context documents specified in the guiding file completely in full without line limits.
   - If executing an implementation plan, also read the `execute` skill instructions using `view_file`.
2. **Continue Execution**:
   - Assess implemented deliverables versus remaining work based on the guiding document and codebase state.
   - Continue execution immediately without stopping or waiting for user instructions.
   - Deliver the execution report strictly adhering to the guiding format (or `execute` skill) upon completion.

---

### Case 2: Other Situations (Not Executing an Implementation Plan)

If NOT currently executing an implementation plan:

1. **Echo Request**: Output the exact verbatim text of the user's most recent request that is still visible in full detail (not compacted).
2. **Report Status**: Report clearly what has been done and what remains unfinished.
3. **Stop & Wait**: Halt execution immediately and wait for user instructions. Do NOT proceed with speculative actions.
