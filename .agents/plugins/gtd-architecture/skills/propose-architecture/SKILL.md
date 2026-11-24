---
name: propose-architecture
description: Propose macro architectural designs for large multi-boundary systems by orchestrating boundary decomposition, shared system invariants, and adjudicated boundary contracts
disable-model-invocation: true
---

# Propose Architecture

Pure dispatcher and decision/escalation bridge on the Main Agent. Delegates macro architectural decomposition, System Spine alignment, and multi-boundary contract design to the `Architecture Orchestrator` subagent.

## 1. Context Resolution & Workspace Setup

1. Generate a kebab-case `<task-name>` slug of maximum three words from the user request.
2. Initialize directory `.gtd/<task-name>/communicate/` directly, overwriting any existing files without pre-checking.
3. Frame the task body for `dispatch_orchestrator.md` from the user's message so an engineer holding only that file can complete the work without asking anything back, dropping orchestration words about delegating:
   - Replace every **reference** — a pointer to a specific item the conversation already pinned down — in place with that item's full content and location.
   - Carry over every **category** — a set whose members the work must find or act on — in the user's own words with where its members live, without listing members you found yourself (when the user named the members, their list is the category and enters verbatim).
   - **When** and only when the user explicitly requests out-of-bounds areas or forbidden mutations, include `## Out of Bounds` stating those exact restrictions; otherwise omit it.
   - Check the drafted `dispatch_orchestrator.md` body by deleting the user's words and the expanded references: if anything remains beyond pure connecting syntax, delete that added material.

- **Completion Criterion**: `.gtd/<task-name>/communicate/` exists, every reference is expanded in place, every category is preserved unenumerated in the user's own words, `## Out of Bounds` is included if and only if explicitly requested by the user, and deleting the user's words and expanded references leaves only pure connecting syntax.

## 2. Dispatch Orchestrator

1. Write the dispatch file to `.gtd/<task-name>/communicate/dispatch_orchestrator.md` matching this physical contract:
   ```markdown
   # Architecture Dispatch: <task-name>

   ## 1. Problem
   <From Step 1: operational reality or user requirements triggering this task>

   ## 2. Objective
   <From Step 1: verifiable external end-state the system must accomplish>

   ## 3. Specification & External Constraints
   - <Expanded references or clickable links to spec/external constraints named by the user; write "None" if not provided>

   ## 4. Context & Starting Points
   - <Categories in the user's own words with where their members live, plus only files/paths explicitly named by the user; write "None" if no prior code applies>

   ## Out of Bounds (include if and only if explicitly requested by the user)
   <From Step 1>
   ```
2. Resolve the absolute path to `<skill-dir>/references/orchestrator_instructions.md` dynamically based on the active platform and workspace environment without reading that file into Main Agent context.
3. Spawn a new `self` subagent with role `Architecture Orchestrator` using this invocation prompt:
   `Execute macro architecture orchestration following <orchestrator_instructions_path> using dispatch context from .gtd/<task-name>/communicate/dispatch_orchestrator.md`

- **Completion Criterion**: `dispatch_orchestrator.md` is written passing Step 1's completion criterion and the `Architecture Orchestrator` subagent is dispatched.

## 3. Decision & Escalation Bridge

Keep the `Architecture Orchestrator` subagent alive whenever it escalates a decision so it resumes without repeating Reality Mapping:

- **When** the Orchestrator escalates a **Macro Axis Gate** or a boundary **`HUMAN_DECISION_REQUIRED`**:
  1. Present the unsettled decision, the concrete consequences of each option, and any artifact link to the user.
  2. Once the user provides a ruling, frame that ruling strictly by Step 1 (expanding every reference in place, preserving categories unenumerated, adding nothing beyond pure connecting syntax) and deliver it back to the **same** `Architecture Orchestrator` subagent via `send_message` so execution resumes.
- **When** the Orchestrator escalates **`CIRCUIT_BREAKER_TRIGGERED`**:
  1. Surface the contradiction summary, physical evidence, and clickable artifact link to the user.
  2. Request the human resolution and stop until the user responds.

- **Completion Criterion**: Every decision escalation is relayed to the user and returned via `send_message` framed by Step 1 to the paused Orchestrator, or a circuit-breaker contradiction is surfaced cleanly to the user.

## 4. Physical Handoff, Idle Retention & Follow Up

1. Upon receiving completion confirmation from the `Architecture Orchestrator`, output strictly the single clickable markdown link: `[.gtd/<task-name>/architectural_proposal.md](file://...)`, leave the `Architecture Orchestrator` subagent in idle state without killing it via `manage_subagents`, and wait for the user's next request.
2. **When** the user requests a follow-up adjustment after reviewing `architectural_proposal.md`, send only the new directive framed by Step 1 to the existing idle `Architecture Orchestrator` via `send_message`.
