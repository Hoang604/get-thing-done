---
name: review-plan
description: Review an implementation plan against boundary-plan principles via plan-reviewer
disable-model-invocation: true
---

1. Take the plan the user names. When the user names none, take the most recent `implementation_plan.md` in this conversation. When none exists, ask the user for its path.
2. Write the **request**: what the user wants from the work this plan serves, and every decision the user made about it in this conversation. Write it to pass the **cold read**: an engineer holding only the request, with no chat history, understands it without asking back. So every reference to the conversation is expanded into its full content, and where the user changed a decision, only the final one stands. Every sentence states something the user said or decided, so that the reviewer reconstructs the plan's reading of the request (its users, jobs, scenarios, and the reasons for its choices) on its own. When this conversation holds no request for the plan, ask the user for one.

   *Completion criterion*: the request passes the cold read, and each of its sentences traces to a message of the user.
3. Dispatch `plan-reviewer` via `invoke_subagent`:
   - **TypeName**: `plan-reviewer`
   - **Role**: `Plan Reviewer`
   - **Prompt**:
     ```markdown
     Review the implementation plan at <plan-link>.

     ### Request
     <the request from step 2>
     ```

   `<plan-link>` is the absolute `file://` path of the plan. The prompt carries only the plan and the request; the subagent's definition carries the whole protocol.
4. Surface Dispatched Prompt:
   Immediately after dispatching, output the exact verbatim prompt sent to `invoke_subagent` into the conversation inside a blockquote (`>`), word for word with zero alterations or omissions.

   *Completion criterion*: the conversation contains the verbatim prompt sent to `invoke_subagent` inside a blockquote (`>`), exactly matching the dispatched text.
5. When the subagent replies, read the review it names and give the user its link, the verdict, and the count of findings for each principle.

*Completion criterion*: the review exists and the user has its link, verdict, and counts.
