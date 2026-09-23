---
name: craft-solution
description: Orchestrate an autonomous council to craft, audit with fresh adversarial auditors on each cycle, and refine architectural solution proposals without bloating parent context
disable-model-invocation: true
---

# CORE DIRECTIVE

Orchestrate architectural solution design by dispatching the dedicated `solution-crafter` subagent, iteratively vetting drafts using a fresh `proposal-auditor` instance on each cycle, and presenting the final proposal without bloating the parent context.

---

## 1. Context Aggregation & Initial Dispatch

1. **Materialize Context**:
   - Collect authentic user intent free of synthetic constraints.
   - Collect all related context files discovered during upstream exploration.
   - Bind your active conversation ID (`<parent-conversation-id>`).

2. **Dispatch Solution Crafter**:
   Invoke `solution-crafter` via `invoke_subagent`:

   ```markdown
   ### 1. Delegation Context
   - Parent Conversation ID: <Active parent conversation ID>
   - Authentic User Intent: <Exact user goal and success criteria, free of synthetic constraints>
   - Related Context Files:
     - <Path to related file 1>
     - <Path to related file 2>
     - <All other files discovered during upstream exploration>

   ### 2. Primary Objective
   Craft, draft, and deliver an architectural solution proposal strictly adhering to the methodology and artifact structure defined in your system prompt.
   ```

- **Completion Criterion**: `invoke_subagent` dispatched to `solution-crafter`.

---

## 2. Orchestrated Convergence Loop (Fresh Auditor Invariant)

When `solution-crafter` reports draft completion (`Completed: Draft solution_proposal.md ready for audit`):

1. **Spawn Fresh Auditor**:
   Invoke a new instance of `proposal-auditor` with clean context (Fresh Auditor Invariant):

   ```markdown
   Audit the architectural proposal located at:
   <appDataDir>/brain/<parent-conversation-id>/solution_proposal.md
   ```

2. **Evaluate Audit Report**:
   When `proposal-auditor` finishes and copies `proposal_audit_report.md` to `<appDataDir>/brain/<parent-conversation-id>/proposal_audit_report.md`:
   - Check the executive verdict inside the report:
     - **If Verdict is APPROVED (Zero Disparities)**: Terminate loop immediately. Kill the auditor subagent.
     - **If Disparities or Inflatons Detected**:
       - Kill the finished auditor instance via `manage_subagents` to ensure complete context disposal.
       - Send a minimal follow-up directive to the active `solution-crafter` via `send_message`:
         `Audit report delivered at <appDataDir>/brain/<parent-conversation-id>/proposal_audit_report.md. Please inspect the reported disparities and refine solution_proposal.md.`
       - Wait for `solution-crafter` to report refinement completion.
       - Spawn a NEW, fresh `proposal-auditor` instance (Audit cycle 2).

3. **Hard Limit**:
   Perform at most 2 auditor invocations (maximum 3 proposal drafts total). Terminate the loop immediately when zero disparities remain or the hard limit is reached.

---

## 3. Silent Handoff & Hard Stop

Upon loop termination:

1. **Cleanup**: Terminate any remaining background subagents using `manage_subagents`.
2. **Zero Context Ingestion**: Do not read, inspect, or summarize `solution_proposal.md` into the chat stream.
3. **Physical Handoff**: Output strictly a concise completion notice in the active conversation language containing the clickable link `[solution_proposal.md](file://<appDataDir>/brain/<parent-conversation-id>/solution_proposal.md)` and invite the user to review the proposal.
4. **Hard Stop**: Terminate execution immediately.
