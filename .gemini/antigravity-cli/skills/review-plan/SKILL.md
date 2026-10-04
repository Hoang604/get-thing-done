---
name: review-plan
description: Review an implementation plan against boundary-plan principles via plan-reviewer
disable-model-invocation: true
---

1. Take the plan the user names. When the user names none, take the most recent `implementation_plan.md` in this conversation. When none exists, ask the user for its path.
2. Dispatch `plan-reviewer` via `invoke_subagent`:
   - **TypeName**: `plan-reviewer`
   - **Role**: `Plan Reviewer`
   - **Prompt**: `Review the implementation plan at <plan-link>.`

   `<plan-link>` is the absolute `file://` path of the plan. The prompt is exactly this sentence; the subagent's definition carries the whole protocol.
3. When the subagent replies, read the review it names and give the user its link, the verdict, and the count of findings for each principle.

*Completion criterion*: the review exists and the user has its link, verdict, and counts.
