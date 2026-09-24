---
name: craft-solution
description: Orchestrate architectural solution design by delegating to an autonomous self subagent to craft and audit proposals without bloating parent context
disable-model-invocation: true
---

# CORE DIRECTIVE

Delegate architectural solution design to an autonomous `self` subagent. The subagent follows the instructions in `crafter_instructions.md` to research, draft, and iteratively audit the proposal, while preserving the parent agent's context completely clean.

---

## 1. Context Resolution & Dispatch

1. **Resolve Paths**:
   - Locate the absolute path to this skill's reference file: `<skill-dir>/references/crafter_instructions.md` (dynamically resolve based on active platform and workspace environment).
   - Collect authentic user intent (task) free of synthetic constraints.
   - Collect absolute paths of all upstream context files discovered during research.
   - Bind your active conversation ID (`<parent-conversation-id>`).

2. **Dispatch Autonomous Subagent**:
   Invoke a `self` subagent via `invoke_subagent`:
   - `TypeName`: `self`
   - `Role`: `Solution Architect`
   - `Prompt`:
     ```markdown
     ### Task
     <Authentic user intent and success criteria, free of synthetic constraints>

     ### Files Path
     - Reference: <Resolved absolute path to crafter_instructions.md>
     - Context Files:
       - <Absolute path to context file 1>
       - <Absolute path to context file 2>
     - Parent Conversation ID: <parent-conversation-id>
     ```

- **Completion Criterion**: `invoke_subagent` dispatched to `self`.

---

## 2. Silent Handoff & Hard Stop

When `self` subagent completes and returns its single confirmation line:

1. **Cleanup**: Terminate the `self` subagent via `manage_subagents`.
2. **Zero Context Ingestion**: Do not read, inspect, or summarize `solution_proposal.md` into the chat stream.
3. **Physical Handoff**: Output strictly a concise completion notice in the active conversation language containing the clickable link `[solution_proposal.md](file://<appDataDir>/brain/<parent-conversation-id>/solution_proposal.md)` and invite the user to review the proposal.
4. **Hard Stop**: Terminate execution immediately.
