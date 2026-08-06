---
name: execute
description: Execute an Alignment Contract.
disable-model-invocation: true
---

## Execution Constraints

- **Singular Path**: Mutate only targets explicitly listed in the Alignment Contract. If the locked technical choices are impossible (e.g., invalid API), halt execution and request a contract amendment.
- **Red Loop**: Before invoking tools to fix a failing verification command, output: (1) the shortest decisive error string, (2) 1-2 present-tense action fragments explaining your inference, and (3) your `<verb> <targets>` declare line (per CRITICAL INSTRUCTION 4).
