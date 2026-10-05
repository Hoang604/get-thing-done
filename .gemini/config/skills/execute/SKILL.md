---
name: execute
description: Execute an implementation plan. Read before starting to implement a plan.
---

## Core Principles

1. **Contract as Anchor**: The approved Plan/Contract defines the core intent, deliverables, and primary target files.
2. **Autonomous Adaptation with Full Disclosure**: Software boundaries are fluid. When completing contracted deliverables uncovers unlisted structural dependencies or upstream defects required for correctness, remediate them cleanly at the source and disclose every deviation. Reject local defensive bypasses or suppressed failures.
3. **True Blockers (Hard Stop)**: Stop execution immediately and escalate to the user only when encountering:
   - **Goal Invalidation**: The contract's core objective is contradictory, unworkable, or fundamentally flawed.
   - **Plan Veto**: The auditor issues a PLAN VETO identifying an architectural flaw in the plan.
   - **Destructive Blast Radius**: Required actions cause irreversible state loss, corrupt historical schema/data parity, or break contracts outside target scope.
   - **Missing External Input**: Missing secrets, unresolvable credentials, or ambiguous business decisions that cannot be deduced from codebase context.
   - **Oscillation Stalemate**: An unresolvable ping-pong loop (e.g., reverting code $A \to B \to A$ across audit rounds) where resolution is ambiguous or involves conflicting architectural constraints.
4. **Accountability Contract**: Any deviation from the explicit plan—unlisted files modified, interface adaptations, or pragmatic fixes—is recorded in the Implementation Ledger the moment it is made; the final report draws its deviations from the ledger.
5. **The Users' Jobs as Scope**: The **users** are everything that consumes an outcome of the contracted deliverables: whatever invokes them and whatever receives what they produce. A user is not necessarily a person; programs that call them, parse their output, or read what they store are users too. Each user's **job** is what it is trying to get done with that outcome. **Friction** is any moment where a user must know, guess, or do something its job does not require. A deliverable is finished when every user completes its job without friction. Removing friction from a user's job is contracted work; serving a different job is scope creep.

## Implementation Ledger

`<plan-dir>/implementation_ledger.md` is the single record of how the implementation departs from the plan. Create it when Build starts and only append to it: never edit or remove an entry. Round 0 holds every deviation made before the first audit round, through Build and Dogfood: each file modified outside the plan's File Manifest and each declared contract adapted. Each audit round appends its own entry, whose Remediations hold the deviations made after it.

```markdown
- **Round 0 — Build Deviations**:
  - [notes.py](file:///path/to/notes.py#L10-L30): <why the change required this file outside the File Manifest, or which declared contract was adapted and why>
- **Round <N>**:
  - **Audit Report**: [audit_report_round_<N>.md](file:///path/to/audit_report_round_<N>.md)
  - **Verdict**: `FAIL` | `PASS` | `PLAN VETO`
  - **Remediations**: `<observed issue>` -> `<code fix applied & target file>`
  - **Oscillation Status**: `None` | `<description of cyclic change (A -> B -> A) and resolution>`
```

When nothing departs from the File Manifest before Round 1, Round 0 holds the single line `None (strict adherence to File Manifest)`.

## Execution Steps

1. **Build**: Implement each milestone, resolving every unlisted adjacent file the contracted objective requires cleanly at the root cause and recording the adaptation in the Implementation Ledger.
   - *Completion criterion*: Every contracted deliverable implemented and self-consistent across the codebase.
2. **Dogfood**: Use the product as each of its users, through its real entrypoint, along every use scenario the plan declares. Take each user's position: want only what that user wants and know only what that user knows, setting aside what you know about the internals. When the plan declares no scenarios, derive them from the plan's objective: follow every outcome to whatever invokes it and whatever receives it to find the users, then walk each user's path through every state the product can be in when its job is attempted. For each scenario, invoke it literally and compare the observed response with the expected one. Every mismatch and every friction is a defect: fix it at the root cause and re-run the scenario. Run baseline checks as often as fixes require.
   - *Completion criterion*: A final pass over every scenario of every user in which every observed response matches its expectation and no friction is found, with each invocation and its observed response recorded for the report, and the ledger's Round 0 lists every deviation made through Build and Dogfood.
3. **Verify & Remediate (Red Loop)**: Execute verification declared in the contract:
   - Execute baseline check commands directly to verify system invariants and runtime execution.
   - **Subagent Audit Gate**: Dispatch the auditor subagent for independent passive code inspection ONLY IF a `Subagent Spawn Directive` is explicitly declared in the approved plan. On initial run (Round 1), dispatch requesting `audit_report_round_1.md` with the ledger link. If directive is absent, do NOT invoke subagents.
   - **Audit Round Protocol**:
     - *Round Entry*: When audit round N returns, append its Round N entry to the Implementation Ledger.
     - *Oscillation Check (Ping-Pong Guard)*: If current remediation reverts an earlier turn's change (e.g., $A \to B \to A$), log the conflict in the round's Oscillation Status. If straightforward, fix and continue; if ambiguous or complex, trigger a Hard Stop and escalate to user.
     - *Re-invocation*: Dispatch `boundary-auditor` for Round $N+1$ passing `<plan-link>`, `audit_report_round_<N+1>.md`, and the ledger link.
   - Track cycles against the plan's declared **Audit Budget** (`<integer> | unlimited`). If the budget is exhausted without a pass, trigger an immediate Hard Stop.
   - When checks fail, fix the root cause immediately—whether within primary targets or in adjacent unlisted files.
   - When a remediation changes behavior on a scenario's path, re-run that scenario before the next audit round.
   - If a True Blocker is reached or the auditor issues a PLAN VETO, halt execution immediately without writing or updating `walkthrough.md`. Report findings directly to the user without attempting autonomous remediation.
   - *Completion criterion*: Verification commands pass, declared audit reports confirm contract compliance with zero plan vetoes, and every scenario touched by remediation has been re-run clean.
4. **Report**: Overwrite `<appDataDir>/brain/<conversation-id>/walkthrough.md` strictly upon successful verification pass. Never create or update `walkthrough.md` on Plan Veto or unverified halts.
   - *Completion criterion*: `walkthrough.md` exists and matches the mandatory schema with all delivered changes, verification proofs, the dogfood record, deviations & adjustments, and diagnostics recorded.

## Constraints & Anti-Rationalization

### Common Rationalizations and Correct Actions

1. *"Plan is flawed, I'll switch to a better approach"* $\rightarrow$ **Incorrect**. Changing architecture or design mid-flight without user alignment creates confusion.
   - **Correct**: Hard Stop immediately; explain why the plan is unworkable and wait for user alignment.
2. *"The plan underestimated blast radius, let me find a clever workaround to cram it into allowed files"* $\rightarrow$ **Incorrect**. Monkey-patching, global hacks, or contrived workarounds produce technical debt.
   - **Correct**: Fix the real issue cleanly at the source and record it in the Implementation Ledger, or Hard Stop if the blast radius represents an uncontrollable architectural redesign.
3. *"Just a quick 1-line hack or fallback to bypass"* $\rightarrow$ **Incorrect**. Defensive fallbacks (`??`, `||`, `?.`) mask invariant violations and corrupt downstream state.
   - **Correct**: Fail fast; trace and fix the upstream root cause cleanly.
4. *"A user might also want this other capability"* $\rightarrow$ **Incorrect** when it serves a different job.
   - **Correct**: Test it against the users' jobs. Friction removed from a user's job is built; a capability serving a different job is recorded under `Out-of-Job Observations` for the user to decide.
5. *"Tests pass, so the deliverable is done"* $\rightarrow$ **Incorrect**. Tests prove the contract; dogfooding proves the jobs.
   - **Correct**: Dogfood every scenario of every user through the real entrypoint and fix every friction found.
6. *"This is a broken past migration; I must fix it to unblock verification"* $\rightarrow$ **Incorrect**. Modifying historical migrations corrupts deployment history and breaks database parity.
   - **Correct**: Hard Stop immediately; report the broken legacy migration and ask the user how to proceed.
7. *"Fix out-of-scope tests by weakening assertions or masking failures"* $\rightarrow$ **Incorrect**. Weakening assertions or silently skipping tests creates false confidence.
   - **Correct**: Fix the underlying root cause in code/fixtures and log the adaptation. Never alter assertions of unrelated tests.
8. *"I will silently fix adjacent syntax/types as a courtesy without logging"* $\rightarrow$ **Incorrect**. Unrecorded mutations violate auditability.
   - **Correct**: Cleanly resolve adjacent blockers, and record every unlisted file in the Implementation Ledger the moment you modify it.
9. *"I will use default system walkthrough headings (`Changes made`, `What was tested`, `Validation results`)"* $\rightarrow$ **Incorrect**. Default system walkthrough headings are strictly forbidden under `/execute`.
   - **Correct**: Overwrite `walkthrough.md` exclusively with the `### Execution & Verification Report` schema.

## Final Output Format

> [!IMPORTANT]
> The schema below is the ONLY permitted format for `walkthrough.md`. Do NOT use default system walkthrough headings (`Changes made`, `What was tested`, `Validation results`).

```markdown
### Execution & Verification Report

#### 1. Changes Delivered
- **Outcome:** <Core capability delivered or bug resolved, with observable evidence if applicable>

| Action | Target | Summary of Change |
| :--- | :--- | :--- |
| `NEW` \| `MOD` \| `DEL` | [<file>](file:///path/to/file#L...) | <Concise summary of changes> |

#### 2. Verification Proof
- **Baseline Check:** `<Exact command(s) executed for verification>` -> `<Passing output summary line / exit code>`
- **Subagent Audit:** <[audit_report_round_<N>.md](file://<appDataDir>/brain/<conversation-id>/audit_report_round_<N>.md) -> `<Verdict: PASS / FAIL / PLAN VETO>` | "N/A (Not declared in plan)">

#### 3. Dogfood Record
- **Users & Jobs:**
  - <User>: <The job this user gets done>

| # | User | Product State | Invocation | Observed Response (final pass) | Friction Found -> Fix |
| :--- | :--- | :--- | :--- | :--- | :--- |
| S-01 | <User> | <State on the user's path> | `<Literal invocation>` | <Observed response> | <Friction and root-cause fix with [file](file:///path#L...)> \| "None" |

- **Out-of-Job Observations:**
  <!-- Capabilities noticed while dogfooding that serve a different job, left for the user to decide. If none: "None". -->
  - <Observation and the job it would serve>

#### 4. Deviations & Diagnostics

- **Scope Deviations & Adjustments:**
  <!-- Every Round 0 entry and every Remediation outside the File Manifest from [implementation_ledger.md](file:///path/to/implementation_ledger.md). If none: "None (Strict adherence to plan)". -->
  - [<file>](file:///path/to/file#L...): <What was adjusted beyond initial plan and rationale for resolving autonomously>

- **Diagnostics & Fixes:**
  <!-- Concise log of failures encountered during verification and remediation applied. If clean on first run: "None (Clean pass)". -->
  - `<Target or Command>`: `<Failure/Error summary>` -> <Root cause and remediation applied>
```
