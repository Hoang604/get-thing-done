---
name: craft-solution
description: Orchestrate architectural solution design by delegating to an autonomous general-purpose subagent to craft and audit proposals without bloating parent context
disable-model-invocation: true
---

# CORE DIRECTIVE

Delegate architectural solution design to an autonomous `general-purpose` subagent. The subagent follows the instructions in `crafter_instructions.md` to research, draft, and iteratively audit the proposal, while preserving the parent agent's context completely clean.

---

## 1. Context Resolution & Dispatch

1. **Resolve Paths & Context**:
   - Locate the absolute path to this skill's reference file: `<skill-dir>/references/crafter_instructions.md` (dynamically resolve based on active platform and workspace environment).
   - Collect absolute paths of all upstream context files discovered during research.
   - Bind your active conversation ID (`${CLAUDE_SESSION_ID}`).

2. **Formulate Task Prompt (Problem-Solution Boundary Principle)**:
   You - the dispatcher - own the **Problem Space**; the `Solution Architect` subagent owns 100% of the **Solution Space**. De-reference chat context into an explicit task constructed strictly as follows:
   - **Problem**: State strictly the operational reality triggering the task: observed system behavior or authentic user requirements. Describe only what is, never what the codebase is missing or should become.
   - **Objective**: Define the end-state exclusively by external verifiable behavior — what the system accomplishes for its use cases without specifying internal implementation.

3. **Dispatch Autonomous Subagent**:
   Invoke a `general-purpose` subagent via `Agent`:
   - `subagent_type`: `general-purpose`
   - `description`: `Solution Architect`
   - `prompt`:
     ```markdown
     ### Task
     Read the reference file and strictly follow its instructions to fulfill:

     **Problem**:
     <Operational reality: observed system behavior or authentic user requirements>

     **Objective**:
     <External verifiable behavior: what the system accomplishes for its use cases>

     ### Files Path
     - Reference: <Resolved absolute path to crafter_instructions.md>
     - Context Files:
       - <Absolute path to context file 1>
       - <Absolute path to context file 2>
     - Parent Conversation ID: ${CLAUDE_SESSION_ID}
     ```

- **Completion Criterion**: `Agent` dispatched to `general-purpose`.

---

## 2. Silent Handoff & Hard Stop

When `general-purpose` subagent completes and returns its single confirmation line:

1. **Cleanup**: Terminate the `general-purpose` subagent via `TaskStop`.
2. **Zero Context Ingestion**: Do not read, inspect, or summarize `solution_proposal.md` into the chat stream.
3. **Physical Handoff**: Output strictly a concise completion notice in the active conversation language containing the clickable link `[solution_proposal.md](file://~/.claude/gtd-brain/${CLAUDE_SESSION_ID}/solution_proposal.md)` and invite the user to review the proposal.
4. **Hard Stop**: Terminate execution immediately.
