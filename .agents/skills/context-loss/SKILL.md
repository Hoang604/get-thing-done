---
name: context-loss
description: You must read this skill immediately via view_file whenever context compaction occurs before calling any other tool or executing any task.
---

# Context Loss Recovery Protocol

This skill is activated immediately when context has been compacted or previous context is lost.

## Strict Prohibitions

1. **Transcript Inspection Prohibition**: NEVER run any command or tool to inspect, search, or read `transcript.jsonl`, `transcript_full.jsonl`, or conversation logs under any circumstances unless the user explicitly asks for it.
2. **Git Command Prohibition**: NEVER run any `git` command (`git status`, `git diff`, `git log`, etc.) unless the user explicitly asks for it.

---

## Recovery Workflow

Inspect the most recent visible user request in full detail (not compacted).

### Case 1: Most Recent Message is `/execute` (or Contains `/execute`)

If the latest visible user request is `/execute` or requests execution of an implementation plan:

1. **Locate and Read Implementation Plan**:
   - Locate the approved implementation plan artifact (`implementation_plan.md` in `<appDataDir>/brain/<conversation-id>/implementation_plan.md` or referenced in workspace).
   - Read the implementation plan file completely using `view_file`.
2. **Read Execute Skill**:
   - Read the `execute` skill instructions using `view_file`.
3. **Continue Execution**:
   - Assess implemented deliverables versus remaining work based on the codebase state.
   - Continue execution immediately without stopping or waiting for user instructions.
   - Deliver the execution report strictly adhering to the `execute` skill format upon completion.

---

### Case 2: Other Messages (Not `/execute`)

If the latest visible user request is NOT `/execute`:

1. **Echo Request**: Output the exact verbatim text of the user's most recent request that is still visible in full detail (not compacted).
2. **Report Status**: Report clearly what has been done and what remains unfinished.
3. **Stop & Wait**: Halt execution immediately and wait for user instructions. Do NOT proceed with speculative actions.
