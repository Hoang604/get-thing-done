---
name: execute
description: Execute an implementation plan through build, scenario evaluation, and verification.
---

## Core Principles

1. **Contract as Anchor**: The approved Plan/Contract defines the core intent, deliverables, and primary target files.
2. **Autonomous Adaptation with Full Disclosure**: **When** completing a deliverable requires touching an unlisted file or adapting a call site so the plan's contracts and invariants hold across the codebase, apply the change and record it in the Implementation Ledger the moment it is made. A ledger entry records how unlisted code was brought into compliance with the plan's contracts and invariants; never record a change that admits inputs or states the plan's invariants exclude, re-computes a value the plan centralizes, or relaxes a test assertion as a deviation or fix—if a codebase constraint prevents a declared contract and invariant from holding together, trigger a Hard Stop as a True Blocker.
3. **True Blockers (Hard Stop)**: Stop execution immediately and escalate to the user only when encountering:
   - **Goal Invalidation**: The contract's core objective is contradictory, unworkable, or fundamentally flawed.
   - **Plan Veto**: The auditor issues a PLAN VETO identifying an architectural flaw in the plan.
   - **Destructive Blast Radius**: Required actions cause irreversible state loss, corrupt historical schema/data parity (including modifying historical migrations), or break contracts outside target scope.
   - **Missing External Input**: Missing secrets, unresolvable credentials, or ambiguous business decisions that cannot be deduced from codebase context.
   - **Oscillation Stalemate**: An unresolvable ping-pong loop (e.g., reverting code $A \to B \to A$ across audit rounds) where resolution is ambiguous or involves conflicting architectural constraints.
4. **The Users' Jobs as Scope**: A deliverable is finished when every user completes its job without friction. Removing friction from a user's job is contracted work; a capability noticed during evaluation that serves a different job is recorded under `Out-of-Job Observations` in the ledger for the user to decide.

## Implementation Ledger

`<plan-dir>/implementation_ledger.md` is the single record of the execution run and how the implementation departs from the plan. Create it when Build starts and only append to it: never edit or remove an entry. Round 0 holds every deviation made before the first audit round, through Build and Scenario Evaluation (each file modified outside the plan's File Manifest and each declared contract adapted, governed by Core Principle 2), any friction or invariant violation fixed during Scenario Evaluation, and any out-of-job observations. Each audit round appends its own entry, whose Remediations hold the deviations made after it. **When** the user interrupts execution and changes how it proceeds, append a User Direction entry at that moment: what the user directed, written so it reads without the conversation, and the reason the user gave, or `None given` when the user gave none. Append the `Verification` entry once all baseline checks and audit rounds pass.

```markdown
- **Round 0 — Build Deviations**:
  - [notes.py](file:///path/to/notes.py#L10-L30): <why the change required this file outside the File Manifest, or which declared contract was adapted and why> | `None (strict adherence to File Manifest)`
  - **Scenario & Invariant Fixes**: `<S-xx / I-xx friction or violation>` -> `<root-cause fix at [file:line](file:///...)>` | `None (all scenarios and invariants held on first pass)`
  - **Out-of-Job Observations**: `<observation and the job it would serve>` | `None`
- **Round <N>**:
  - **Audit Report**: [audit_report_round_<N>.md](file:///path/to/audit_report_round_<N>.md)
  - **Verdict**: `PASS` | `FAIL (CLOSED)` | `FAIL (OPEN)` | `PLAN VETO`
  - **Remediations**: `<observed issue>` -> `<code fix applied & target file>`
  - **Rejections**: `<finding>` -> `<evidence it fails, with file:line>` | `None`
  - **Oscillation Status**: `None` | `<description of cyclic change (A -> B -> A) and resolution>`
- **User Direction** (during <Build milestone N | Scenario Evaluation | Round N>):
  - **Directed**: <what the user told you to do instead, and what it replaces in the plan>
  - **Reason**: <the reason the user gave> | `None given`
- **Verification**:
  - **Baseline Checks**: `<exact command(s) executed>` -> `<passing output summary / exit code>`
  - **Unplanned Decisions & Residual Branches**: [file.ts](file:///path/to/file.ts#L10-L20): `<every branch, default value, or retained state in the modified functions not specified by the plan, the input condition that reaches it, and why it is required>` | `None (every branch, default, and state in modified functions is specified by the plan)`
```

## Execution Steps

1. **Build**: For each milestone $N$ in sequence, read only the `#L<start>-L<end>` slices in milestone $N$'s `File Manifest` whose `[MODIFY]` target lines are absent from current context, and write all of milestone $N$'s file changes to disk before reading or editing anything for milestone $N+1$. **When** moving a responsibility from a source site to a target site, delete every computation at the source whose value served only the removed call, and test every early return, initial state, and child state in the target subtree against an input that exercises the newly moved responsibility while leaving the target's prior responsibilities idle, updating any condition or state that still assumes the target's pre-change scope. Upon completing milestone $N$, notify the user that milestone $N$ is finished, and for milestone $N+1$, explicitly state what is going to be done and immediately proceed to execute it (or state the transition to Scenario Evaluation if completing the final milestone).
   - *Completion criterion*: Every milestone's `File Manifest` changes and required unlisted call-site adaptations are written to disk, retired computations at source sites are deleted, and target-subtree guards and states are updated for their new scope, without pausing between milestones.
2. **Scenario Evaluation**: Evaluate the system from the position of each user along every scenario and invariant declared in the plan. Take each user's position: want only what that user wants and know only what that user knows, setting aside internal implementation details. Mentally trace the path from the user's stimulus through the entrypoint to the observable response (or verify via existing automated test commands if available, without launching ad-hoc manual shell environments). Ensure the user receives exactly the expected response and encounters no friction (unnecessary knowledge, confusing errors, or awkward parameters). **When** a scenario or check fails on an input, branch on the structural property that makes that class of inputs require the handling rather than matching the specific values that failed the check, and apply the same handling to every sibling message, computation, or caller in the subsystem that shares that property. Run baseline checks as often as fixes require.
   - *Completion criterion*: Every scenario and invariant verified to produce its expected observable response without user friction, and the ledger's Round 0 lists every deviation, scenario/invariant fix, and out-of-job observation through Build and Scenario Evaluation.
3. **Verify & Remediate (Red Loop)**: Execute verification declared in the contract:
   - Execute baseline check commands directly to verify system invariants and runtime execution.
   - **Subagent Audit Gate**: Dispatch the auditor subagent for independent passive code inspection ONLY IF a `Subagent Spawn Directive` is explicitly declared in the approved plan. On initial run (Round 1), dispatch requesting `audit_report_round_1.md` with the ledger link. If directive is absent, do NOT invoke subagents.
   - **Audit Round Protocol**:
     - *Round Summary*: When audit round N returns, check each of its findings against the code before changing anything, then give the user a summary of the round: the verdict, and for each finding what the auditor claims and whether it holds, fails, or partly holds, with the evidence that decided it (`file:line`). Proceed without waiting: remediate what holds and keep the code against the rest. A PLAN VETO halts as stated below.
     - *Round Entry*: Append the round's Round N entry to the Implementation Ledger, with every finding kept against under Rejections, so the next round's auditor sees the reason.
     - *Oscillation Check (Ping-Pong Guard)*: If current remediation reverts an earlier turn's change (e.g., $A \to B \to A$), log the conflict in the round's Oscillation Status. If straightforward, fix and continue; if ambiguous or complex, trigger a Hard Stop and escalate to user.
     - *Re-invocation*: **When** the round's verdict is `FAIL (CLOSED)` and every finding is remediated to its specified target state with `Rejections: None` and no additional code changes, the audit gate is complete once baseline checks and touched scenarios pass; otherwise dispatch `boundary-auditor` for Round $N+1$ passing `<plan-link>`, `audit_report_round_<N+1>.md`, and the ledger link.
   - Track cycles against the plan's declared **Audit Budget** (`<integer> | unlimited`). If the budget is exhausted without completing the audit gate, trigger an immediate Hard Stop.
   - **When** checks or audit findings require a fix, apply the Scenario Evaluation fix rule (branching on the shared structural property across all sibling members in the subsystem) and Core Principle 2.
   - When a remediation changes behavior on a scenario's path, re-run that scenario and re-probe the invariants spanning it before completing the audit gate or dispatching the next audit round.
   - If a True Blocker is reached or the auditor issues a PLAN VETO, halt execution immediately and report findings directly to the user without attempting autonomous remediation.
   - Once verification passes, check every modified function against the plan to record `Unplanned Decisions & Residual Branches` (deleting any branch or state that is not required), append the `Verification` entry to `implementation_ledger.md`, and reply to the user with the link to `[implementation_ledger.md](file:///...)` (and the final audit report when applicable), a summary of the delivered outcome and baseline check result, and any unplanned decisions, out-of-job observations, or unchecked risks.
   - *Completion criterion*: Verification commands pass, the audit gate completes via `PASS` or a fully remediated `FAIL (CLOSED)` with zero rejections and zero plan vetoes, every scenario touched by remediation (with the invariants spanning it) has been re-run clean, every modified function has been checked against the plan so `implementation_ledger.md` records both the final `Verification` entry and every unplanned branch, default value, or retained state under `Unplanned Decisions & Residual Branches` (deleting any that is not required), and the user has the link to the ledger and the completion summary.
