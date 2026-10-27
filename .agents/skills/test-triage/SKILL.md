---
name: test-triage
description: Classify every test in scope as REAL or JUNK via test-triager
disable-model-invocation: true
---

1. Take the scope from the user's message: the paths they named, the scope they want, or the whole suite when they named none.
2. Dispatch `test-triager` via `invoke_subagent`:
   - **TypeName**: `test-triager`
   - **Role**: `Test Triager`
   - **Prompt**: `Scope: <scope>.`

   The prompt carries the scope; the subagent's definition carries the whole protocol. you should not write anything else to Prompt.
3. When the subagent replies, read the triage report it names with `read_file` and give the user its link with the `REAL` and `JUNK` counts.

*Completion criterion*: the triage report exists and the user has its link and counts.
