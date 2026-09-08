---
name: execute
description: Execute an Alignment Contract.
disable-model-invocation: true
---

## Core Principles

1. **The contract is the task**: The task is defined strictly by the approved Plan/Contract, not the raw initial prompt. Deviating from the plan or editing unlisted files is considered an error.
2. **When to stop and report**: Stop execution immediately without further edits, and report to the user in these two situations:
   - **Verification failure outside scope**: A verification command fails, and fixing it requires modifying files outside the contract.
   - **Plan invalidation**: You realize before or during execution that the plan is flawed, unworkable, or insufficient to achieve the goal.
3. **Thinking circuit breaker (No mental gymnastics)**: When you realize the plan underestimated the real blast radius, do not spend thinking cycles searching for workarounds to squeeze changes into allowed files. Overthinking how to work around the plan is a direct signal that the plan is outdated. Stop thinking immediately and report the discrepancy.

## Execution Steps

1. **Singular Path**: Mutate only targets explicitly listed in the Alignment Contract.
2. **Verify**: Run verification commands.
   - If fail + fix is strictly within contract scope: execute **Red Loop**.
   - If verification fails outside scope or plan is invalidated: execute **Hard Stop**.
3. **Report**: Overwrite `<appDataDir>/brain/<conversation-id>/walkthrough.md` with the report below. Do not print to chat or re-summarize.

## Constraints & Anti-Rationalization

- **Red Loop**: Before invoking tools to fix an in-scope error, output: (1) shortest decisive error string, (2) 1-2 present-tense action fragments explaining inference, and (3) `<verb> <targets>` declare line.
- **Hard Stop**: Halt all modifications immediately. State exact error or defect. Wait for user contract amendment.

### 6 Common Rationalizations and Correct Actions

1. *"Fix out-of-scope targets to make tests pass"* $\rightarrow$ **Incorrect**. A passing test does not justify expanding scope.
   - **Correct**: Stop immediately; report the failing command and the out-of-scope cause.
2. *"Plan is flawed, I'll switch to a better approach"* $\rightarrow$ **Incorrect**. Changing design mid-flight without user alignment creates confusion.
   - **Correct**: Stop immediately; explain why the plan is unworkable and wait for a revised plan.
3. *"The plan underestimated blast radius, let me find a clever workaround to cram it into allowed files"* $\rightarrow$ **Incorrect**. Mental gymnastics produce convoluted anti-patterns and technical debt.
   - **Thought example**: *"Plan only allows modifying `UserCard`, but needed data is in `authStore`. If I can't touch the store, maybe I can parse localStorage directly or hack a global window event..."*
   - **Correct**: Cut the thought immediately. Report: *"The plan underestimated the blast radius: `UserCard` requires changes to `authStore` which is outside the contract targets. Please update the plan."*
4. *"User just wants it to work (Helpful savior)"* $\rightarrow$ **Incorrect**. The contract defines the scope, not speculative user intent.
   - **Correct**: Keep strictly to contract boundaries; do not assume approval beyond the plan.
5. *"Just a quick 1-line hack or fallback to bypass"* $\rightarrow$ **Incorrect**. Masks real errors and bypasses invariant checks.
   - **Correct**: Fail fast; do not add silent defaults or bypasses.
6. *"Already started, keep patching downstream issues"* $\rightarrow$ **Incorrect**. Expands blast radius uncontrollably.
   - **Correct**: Stop immediately; report the unexpected scope expansion to the user.

## Final Output Format


```markdown
### Execution & Verification Report

#### 1. Changes Delivered
- **Outcome:** <Core capability delivered or bug resolved, with observable evidence if applicable>

| Action | Target | Summary of Change |
| :--- | :--- | :--- |
| `NEW` \| `MOD` \| `DEL` | [<file>](file:///path/to/file#L...) | <Concise summary of changes> |

#### 2. Verification Proof
- **Baseline Check:** `<Exact command(s) executed for verification>` -> `<Passing output summary line / exit code>`

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

