---
name: execute
description: Execute an Alignment Contract.
disable-model-invocation: true
---

## Core Principles

1. **The contract is the task**: The task is defined strictly by the approved Plan/Contract, not the raw initial prompt. Deviating from the plan or editing unlisted files is considered an error.
2. **Target File Whitelist**: The contract targets constitute a strict, finite whitelist of file paths. Any file not explicitly listed in the contract is out-of-scope by definition. There are zero exceptions for:
   - Legacy or pre-existing migration scripts.
   - Pre-existing failing tests or broken environment fixtures.
   - Files cited in verification stacktraces or compiler errors.
   - "Obvious" DDL or syntax fixes.
3. **When to stop and report**: Stop execution immediately without further edits, and report to the user in these situations:
   - **Verification failure outside whitelist**: A verification command fails, and the root cause or required fix is in a file not listed in the contract whitelist.
   - **Environmental / pre-existing blocker**: A command is blocked by existing codebase bugs (e.g. failing past migrations, broken build scripts) outside contract targets.
   - **Plan invalidation**: You realize before or during execution that the plan is flawed, unworkable, or insufficient to achieve the goal.
4. **Thinking circuit breaker (No mental gymnastics)**: When you realize the plan underestimated the real blast radius, do not spend thinking cycles searching for workarounds to squeeze changes into allowed files. Overthinking how to work around the plan is a direct signal that the plan is outdated. Stop thinking immediately and report the discrepancy.

## Execution Steps

1. **Singular Path**: Mutate only targets explicitly listed in the Alignment Contract whitelist.
2. **Verify**: Execute verification declared in the plan:
   - Run baseline check commands.
   - If the plan contains a Subagent Spawn Directive, dispatch the auditor subagent and ingest its report upon completion.
   - **Pre-Red-Loop Whitelist Gate**: If verification fails (command error or subagent `FAIL` verdict), check:
     - Is the file to be modified explicitly present in the Contract Target Whitelist?
     - If **YES**: Execute **Red Loop**.
     - If **NO**: **Red Loop is strictly forbidden**. Execute **Hard Stop** immediately.
   - If plan is invalidated or environmental blocker occurs: Execute **Hard Stop**.
3. **Report**: Overwrite `<appDataDir>/brain/<conversation-id>/walkthrough.md` strictly with the `Execution & Verification Report` format below.
   - **System Template Override**: Default system walkthrough sections (`Changes made`, `What was tested`, `Validation results`) are strictly forbidden. You must strictly adhere to the `### Execution & Verification Report` schema.
   - Do not print to chat or re-summarize.

## Constraints & Anti-Rationalization

- **Red Loop**: Permissible ONLY on files in the Contract Target Whitelist. Before invoking tools to fix an in-scope error, output: (1) shortest decisive error string, (2) 1-2 present-tense action fragments explaining inference, and (3) `<verb> <targets>` declare line.
- **Hard Stop**: Halt all modifications immediately. State: (1) the failing command, (2) the out-of-whitelist target file causing the failure, and (3) technical root cause. Wait for user contract amendment.

### 8 Common Rationalizations and Correct Actions

1. *"This is an environmental blocker or broken past migration; I must fix it to unblock verification"* $\rightarrow$ **Incorrect**. Unblocking verification does not grant permission to edit unlisted files. Modifying past migrations corrupts deployment history.
   - **Correct**: Hard Stop immediately. Report the failing command, the broken legacy file, and ask the user how to proceed.
2. *"Fix out-of-scope targets to make tests pass"* $\rightarrow$ **Incorrect**. A passing test does not justify expanding scope.
   - **Correct**: Hard Stop immediately; report the failing command and the out-of-scope cause.
3. *"The error is an obvious DDL/syntax mistake, I'll just quickly fix it as a courtesy"* $\rightarrow$ **Incorrect**. "Obvious" fixes outside the whitelist are silent violations.
   - **Correct**: Hard Stop immediately; point out the exact bug in the report and let the user decide.
4. *"Plan is flawed, I'll switch to a better approach"* $\rightarrow$ **Incorrect**. Changing design mid-flight without user alignment creates confusion.
   - **Correct**: Hard Stop immediately; explain why the plan is unworkable and wait for a revised plan.
5. *"The plan underestimated blast radius, let me find a clever workaround to cram it into allowed files"* $\rightarrow$ **Incorrect**. Mental gymnastics produce convoluted anti-patterns and technical debt.
   - **Thought example**: *"Plan only allows modifying `UserCard`, but needed data is in `authStore`. If I can't touch the store, maybe I can parse localStorage directly or hack a global window event..."*
   - **Correct**: Cut the thought immediately. Report: *"The plan underestimated the blast radius: `UserCard` requires changes to `authStore` which is outside the contract targets. Please update the plan."*
6. *"User just wants it to work (Helpful savior)"* $\rightarrow$ **Incorrect**. The contract defines the scope, not speculative user intent.
   - **Correct**: Keep strictly to contract boundaries; do not assume approval beyond the plan.
7. *"Just a quick 1-line hack or fallback to bypass"* $\rightarrow$ **Incorrect**. Masks real errors and bypasses invariant checks.
   - **Correct**: Fail fast; do not add silent defaults or bypasses.
8. *"I will use the default system walkthrough template (`Changes made`, `What was tested`, `Validation results`)"* $\rightarrow$ **Incorrect**. Default system walkthrough templates are strictly forbidden under `/execute`. The skill strictly mandates the `### Execution & Verification Report` schema.
   - **Correct**: Overwrite `walkthrough.md` exclusively with `### Execution & Verification Report` adhering exactly to sections 1, 2, and 3. Zero default system walkthrough sections allowed.

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
- **Subagent Audit:** [audit_report.md](file://<appDataDir>/brain/<conversation-id>/audit_report.md) -> `<Verdict (e.g. ALL PASS)>`

#### 3. Execution Delta & Diagnostics
- **Diagnostic Matrix:**
  <!--
    Rules for Diagnostic Matrix:
    - If zero failures across all runs: Output "None (Clean pass)".
    - Iteration Definition: `Iter` is strictly the 1-indexed verification command execution sequence (`L1` = 1st command run, `L2` = 2nd command run after patch, `Ln` = n-th run).
    - Discrete Errors (Type errors, runtime exceptions, test failures, specific lint blockers): Output an exhaustive row for every failure encountered across all iterations.
    - Mass Mechanical Violations (> 5 identical lint/format issues in a single run): Group into a single quantified summary row (e.g., `67 issues across 20 files | eslint rule violations`).
  -->
  | # | Iter | Target | Error Signature / Code | Root Cause Ref | Status |
  |---|---|---|---|---|---|
  | <1..N> | <L1..Ln> | [<file:line>](file:///path/to/file#L...) | `<ErrorClass / Code / Message>` | <RC-ID> | Resolved/Unsolved |

- **Root Causes:**
  - **<RC-ID>:** <Factual technical explanation of the underlying failure driver or regression mechanism>

- **Resolutions Applied:**
  - [<file:lines>](file:///path/to/file#L...): <Concise summary of remediation applied at each iter>
```

