---
name: craft-solution
description: Orchestrate architectural solution design by delegating to an autonomous self subagent to craft and audit proposals without bloating parent context
disable-model-invocation: true
---

# CORE DIRECTIVE

Delegate architectural solution design to an autonomous `self` subagent. The subagent follows the instructions in `crafter_instructions.md` to research, draft, and iteratively audit the proposal, while preserving the parent agent's context completely clean.

---

## 1. Context Resolution & Dispatch

1. **Resolve Paths & Context**:
   - Locate the absolute path to this skill's reference file: `<skill-dir>/references/crafter_instructions.md` (dynamically resolve based on active platform and workspace environment).
   - Collect absolute paths of all upstream context files discovered during research.
   - Bind your active conversation ID (`<parent-conversation-id>`).

2. **Formulate Task Prompt (Problem-Solution Boundary Principle)**:
   You - the dispatcher - own the **Problem Space**; the `Solution Architect` subagent owns 100% of the **Solution Space**. De-reference chat context into an explicit task constructed strictly as follows:
   - **Problem**: State the authentic condition that necessitates design — what is currently observed or demanded — without proposing any mechanism.
   - **Objective**: Define the end-state exclusively by verifiable capability — what the system must accomplish — leaving the structural means entirely to the architect.
   - **Invariants**: State only constraints that remain non-negotiable across every valid architecture. Any rule prescribing internal design choices belongs to the proposal, not the prompt.

3. **Dispatch Autonomous Subagent**:
   Invoke a `self` subagent via `invoke_subagent`:
   - `TypeName`: `self`
   - `Role`: `Solution Architect`
   - `Prompt`:
     ```markdown
     ### Task
     Read the reference file and strictly follow its instructions to fulfill:

     **Problem**:
     <Authentic condition triggering the task: observed facts or demands>

     **Objective**:
     <Verifiable target capability: what must be accomplished>

     **Invariants**:
     <Non-negotiable constraints that hold across any valid design>

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
