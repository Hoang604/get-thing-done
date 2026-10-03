---
name: verify-issue
description: verify correctness of code review
disable-model-invocation: true
---

1. Take the most recent code-review report in this conversation. When none exists, ask the user for its path.
2. Dispatch `issue-verifier` via `invoke_subagent`:
   - **TypeName**: `issue-verifier`
   - **Role**: `Issue Verifier`
   - **Prompt**: `Verify the code review at <review-link>.`

   `<review-link>` is the absolute `file://` path of the report. The prompt is exactly this sentence; the subagent's definition carries the whole protocol.
3. When the subagent replies, read the verification report it names and give the user its link with the count of each verdict and each class.

*Completion criterion*: the verification report exists and the user has its link and counts.
