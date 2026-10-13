---
name: review-plan
description: Review an implementation plan via plan-reviewer, then adjudicate findings through the challenge protocol to remediate or defend the plan
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
5. **Challenge & Adjudicate Findings**:
   When the subagent replies, read the review report in full with `view_file`. Execute the Challenge Protocol against every finding before reporting:
   - Check each finding and requested change against codebase reality and the task's requirements.
   - **Holds**: The finding is verified by code evidence or explicit requirements. Update `implementation_plan.md` to remediate the finding, citing the confirming `file:line` or requirement text.
   - **Fails**: The finding contradicts code, proposes speculative seams or invalid fallbacks, or misinterprets requirements. Keep the plan unchanged and record the exact refuting code evidence (`file:line`).
   - **Partly holds**: Remediate only the verified part in `implementation_plan.md`; refute and keep the rest.

6. **Present Adjudication**:
   Output the final report to the user formatted as follows:
   - Link to the review report and overall verdict.
   - Link to `implementation_plan.md` (with line references to remediations).
   - **Holds**: Each accepted finding and the exact modification made to the plan.
   - **Fails**: Every rejected finding with its full refutation rationale and code proof, explicitly flagged for potential user overrule.
   - Request the user's confirmation or overrule decisions.

*Completion criterion*: Every finding in the review report is adjudicated as Holds, Fails, or Partly holds; all verified findings are remediated in `implementation_plan.md`; and all rejected findings are presented with refutation citations for user overrule.
