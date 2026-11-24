---
name: test-triage
description: Classify every test in scope as REAL or JUNK via test-triager
disable-model-invocation: true
---

1. Take the scope from the user's message: the paths they named, the scope they want, or the whole suite when they named none.
2. Dispatch `test-triager` via `invoke_subagent`:
   - **TypeName**: `test-triager`
   - **Role**: `Test Triager`
   - **Prompt**: `Scope: <scope>. Standard: <skill-dir>/references/real-test-standard.md` (substitute `<skill-dir>` with this skill's directory).

   The prompt carries only the scope and standard path; the subagent's definition carries the rest of the protocol.
3. When the subagent replies, read the triage report it names with `read_file` and give the user its link with the `REAL` and `JUNK` counts.

*Completion criterion*: the triage report exists and the user has its link and counts.
