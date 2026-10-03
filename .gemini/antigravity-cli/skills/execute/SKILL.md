---
name: execute
description: Execute a implemenation plan. read before start implementing a plan.
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
4. **Accountability Contract**: Any deviation from the explicit plan—unlisted files modified, interface adaptations, or pragmatic fixes—must be fully recorded in the final report.
5. **Generative Realization (Craftsmanship over Nominal Compliance)**: A deliverable is finished only when it works smoothly in real use, without pushing hassle onto the user or adding unrequested features. A contract defines functional intent, not permission to deliver raw scaffolding.

## Execution Steps

1. **Execute Planned Work**: Build each milestone as a finished tool ready for immediate use, so callers and users never have to deal with missing pieces. Fulfill the contract completely by handling all practical details inside. If completing the contracted objective requires touching unlisted adjacent files, resolve them cleanly at the root cause and log the adaptation.
   - *Completion criterion*: All contracted deliverables implemented as complete, working tools self-consistent across the codebase.
2. **Verify & Remediate (Red Loop)**: Execute verification declared in the contract:
   - Execute baseline check commands directly to verify system invariants and runtime execution.
   - **Subagent Audit Gate**: Dispatch the auditor subagent for independent passive code inspection ONLY IF a `Subagent Spawn Directive` is explicitly declared in the approved plan. On initial run (Round 1), dispatch requesting `audit_report_round_1.md`. If directive is absent, do NOT invoke subagents.
   - **Audit Failure & Ledger Protocol**:
     - *Round 1 Failure*: Create `<plan-dir>/audit_ledger.md` logging Round 1: link to `audit_report_round_1.md`, issues addressed, and remediation actions taken.
     - *Subsequent Failures (Round N)*: Append Round N entry to `audit_ledger.md` (**Append-only**: never edit prior entries).
     - *Oscillation Check (Ping-Pong Guard)*: If current remediation reverts an earlier turn's change (e.g., $A \to B \to A$), log the conflict in `audit_ledger.md`. If straightforward, fix and continue; if ambiguous or complex, trigger a Hard Stop and escalate to user.
     - *Re-invocation*: Dispatch `boundary-auditor` for Round $N+1$ passing `<plan-link>`, `audit_report_round_<N+1>.md`, and `[audit_ledger.md](file:///path/to/audit_ledger.md)`.
   - Track cycles against the plan's declared **Audit Budget** (`<integer> | unlimited`). If the budget is exhausted without a pass, trigger an immediate Hard Stop.
   - When checks fail, fix the root cause immediately—whether within primary targets or in adjacent unlisted files.
   - If a True Blocker is reached or the auditor issues a PLAN VETO, halt execution immediately without writing or updating `walkthrough.md`. Report findings directly to the user without attempting autonomous remediation.
   - *Completion criterion*: Verification commands pass and declared audit reports confirm contract compliance with zero plan vetoes.
3. **Report**: Overwrite `<appDataDir>/brain/<conversation-id>/walkthrough.md` strictly upon successful verification pass. Never create or update `walkthrough.md` on Plan Veto or unverified halts.
   - *Completion criterion*: `walkthrough.md` exists and matches the mandatory schema with all delivered changes, verification proofs, deviations & adjustments, and diagnostics recorded.

## Constraints & Anti-Rationalization

### Common Rationalizations and Correct Actions

1. *"Plan is flawed, I'll switch to a better approach"* $\rightarrow$ **Incorrect**. Changing architecture or design mid-flight without user alignment creates confusion.
   - **Correct**: Hard Stop immediately; explain why the plan is unworkable and wait for user alignment.
2. *"The plan underestimated blast radius, let me find a clever workaround to cram it into allowed files"* $\rightarrow$ **Incorrect**. Monkey-patching, global hacks, or contrived workarounds produce technical debt.
   - **Correct**: Fix the real issue cleanly at the source and disclose it in `Deviations & Adjustments`, or Hard Stop if the blast radius represents an uncontrollable architectural redesign.
3. *"Just a quick 1-line hack or fallback to bypass"* $\rightarrow$ **Incorrect**. Defensive fallbacks (`??`, `||`, `?.`) mask invariant violations and corrupt downstream state.
   - **Correct**: Fail fast; trace and fix the upstream root cause cleanly.
4. *"I will add this extra capability because the user might need it"* $\rightarrow$ **Incorrect**. Introducing unrequested business features is scope creep.
   - **Correct**: Scope is an upper bound. Direct all initiative strictly into perfecting the contracted deliverables.
5. *"The plan only asked for the core function, so raw scaffolding is fine"* $\rightarrow$ **Incorrect**. Contracts define intent, not permission to leave rough edges.
   - **Correct**: Build every deliverable to production standards, fully finished so it works smoothly out of the box.
6. *"This is a broken past migration; I must fix it to unblock verification"* $\rightarrow$ **Incorrect**. Modifying historical migrations corrupts deployment history and breaks database parity.
   - **Correct**: Hard Stop immediately; report the broken legacy migration and ask the user how to proceed.
7. *"Fix out-of-scope tests by weakening assertions or masking failures"* $\rightarrow$ **Incorrect**. Weakening assertions or silently skipping tests creates false confidence.
   - **Correct**: Fix the underlying root cause in code/fixtures and log the adaptation. Never alter assertions of unrelated tests.
8. *"I will silently fix adjacent syntax/types as a courtesy without logging"* $\rightarrow$ **Incorrect**. Unrecorded mutations violate auditability.
   - **Correct**: Cleanly resolve adjacent blockers, but record every unlisted file in `Deviations & Adjustments`.
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

#### 3. Deviations & Diagnostics

- **Scope Deviations & Adjustments:**
  <!-- List every out-of-plan change, unlisted file touched, or pragmatic adjustment made to avoid blocking. If none: "None (Strict adherence to plan)". -->
  - [<file>](file:///path/to/file#L...): <What was adjusted beyond initial plan and rationale for resolving autonomously>

- **Diagnostics & Fixes:**
  <!-- Concise log of failures encountered during verification and remediation applied. If clean on first run: "None (Clean pass)". -->
  - `<Target or Command>`: `<Failure/Error summary>` -> <Root cause and remediation applied>

#### 4. Proactive Value Additions

<!-- Record thoughtful touches added to make the feature better to use within the contracted boundary, and why they helped. If none: "None (Strict contract only)". -->
- [<file>](file:///path/to/file#L...): <Thoughtful touch added to make the feature better to use, and why it helped>
```
