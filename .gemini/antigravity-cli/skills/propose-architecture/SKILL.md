---
name: propose-architecture
description: Propose macro architectural approaches for features or subsystems by orchestrating boundary-specific DAG crafters
disable-model-invocation: true
---

# Propose Architecture

Pure dispatcher and escalation bridge on the Main Agent. Delegates architectural decomposition and design to the Architecture Orchestrator subagent.

## 1. Context Resolution & Workspace Setup
1. Generate a kebab-case `<task-name>` slug of maximum three words from the user request.
2. Initialize directory `.gtd/<task-name>/communicate/` directly, overwriting any existing files without pre-checking.
3. Identify the referenced specification file and any code files analyzed in prior conversation turns or tagged in the prompt, that related to the spec.

## 2. Dispatch Orchestrator
1. Write the dispatch file to `.gtd/<task-name>/communicate/dispatch_orchestrator.md` matching this physical contract:
   ```markdown
   # Architecture Dispatch: <task-name>

   ## 1. Specification
   - Spec: [<path-to-spec.md>](file://...)

   ## 2. Starting Points
   - [<path/to/entry_file_1.ts>](file://...)
   - [<path/to/entry_file_2.ts>](file://...)
   ```
2. Resolve the absolute path to this skill's reference file `<skill-dir>/references/orchestrator_instructions.md` dynamically based on the active platform and workspace environment. Don't read this file yourself.
3. Spawn a brand new `self` subagent with role `Architecture Orchestrator` using this standardized invocation prompt:
   `Execute macro architecture orchestration following <orchestrator_instructions_path> using dispatch context from .gtd/<task-name>/communicate/dispatch_orchestrator.md`

## 3. Escalation Bridge
When the Architecture Orchestrator sends an escalation message regarding a circuit-breaker contradiction:
1. Surface the contradiction summary and physical evidence to the user in chat with the clickable artifact link to the failure if the subagent gave it to you.
2. Request the human decision and stop.

## 4. Physical Handoff & Hard Stop
Upon receiving completion confirmation from the Orchestrator, output exclusively the single clickable markdown link: `[.gtd/<task-name>/architectural_proposal.md](file://...)` and wait for user's next request.
