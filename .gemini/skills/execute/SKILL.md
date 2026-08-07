---
name: execute
description: Execute an Alignment Contract.
disable-model-invocation: true
---

## Execution Steps

1. **Singular Path**: Mutate only targets explicitly listed in the Alignment Contract.
2. **Verify**: Run verification commands. End step only when verification cleanly passes.
   - If fail + fix is strictly within contract scope: execute **Red Loop**.
   - If fail + fix requires out-of-scope logic or new targets: execute **Hard Stop**.

## Constraints

- **Red Loop**: Before invoking tools to fix, output: (1) shortest decisive error string, (2) 1-2 present-tense action fragments explaining inference, and (3) `<verb> <targets>` declare line.
- **Hard Stop**: Halt execution immediately. Output exact error. Wait for user contract amendment.
