---
name: execute
description: Execute an Alignment Contract.
disable-model-invocation: true
---

## Execution Steps

1. **Singular Path**: Mutate only targets explicitly listed in the Alignment Contract.
2. **Verify**: Run verification commands.
   - If fail + fix is strictly within contract scope: execute **Red Loop**.
   - If fail + fix requires out-of-scope logic or new targets: execute **Hard Stop**.
3. **Report**: Upon clean verification pass, output the `Execution & Contract Delivery Report` as the final turn output.

## Constraints

- **Red Loop**: Before invoking tools to fix, output: (1) shortest decisive error string, (2) 1-2 present-tense action fragments explaining inference, and (3) `<verb> <targets>` declare line.
- **Hard Stop**: Halt execution immediately. Output exact error. Wait for user contract amendment.

## Final Output Format

```markdown
### Execution & Contract Delivery Report

#### 1. Contract Outcomes Achieved
- **Capability Delivered:** <State what user can now do vs contract item 2.1>
- **Observable Outcome:** <State what user now sees / system output vs contract item 2.2>
- **Targets Delivered:**
  - [<file>](file:///path#L...): <Status: [NEW] | [MODIFY] | [DELETE] completed>

#### 2. Verification Proof
- **Command:** `<exact terminal verification command>`
- **Output:** `<exact passing summary line e.g. '12 passed in 0.45s'>`
- **Validation Proof:** <Observable result confirming acceptance scenario>

#### 3. Execution Delta & Deviations
- **Trigger / Error:** <Exact error string, failing test name, or "None (First-pass clean pass)">
- **Root Cause:** <Decisive 1-2 sentences on what failed and why, or "N/A">
- **Contract Impact:** <"Contained within contract" | "Required contract amendment (Hard Stop resolved)">
- **Resolution Applied:**
  1. [<file:lines>](file:///path#L...): <Exact seam mutation or invariant fix>
```
