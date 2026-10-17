---
name: review-plan
description: Review an implementation plan via plan-reviewer, then adjudicate findings through the challenge protocol to remediate or defend the plan
disable-model-invocation: true
---

1. Resolve the target plan: take the plan the user names; when the user names none, take the most recent `implementation_plan.md` in this conversation; when none exists, ask the user for its path.

   *Completion criterion*: the target plan's path is resolved, or the turn ends asking the user for it.
2. Write the **request**: state every goal and final decision the user expressed for the work this plan serves in self-contained prose that passes the **cold read** — an engineer given only the request and the codebase has everything needed to reconstruct the task on the first read. Expand every reference to the conversation into its full concrete content, keep only the final decision where the user changed course, and state only what the user said or decided so the reviewer reconstructs the plan's reading of the request (its users, jobs, scenarios, and reasons for its choices) independently. When this conversation holds no request for the plan, ask the user for one.

   *Completion criterion*: the request passes the cold read and each of its sentences traces to a message of the user, or the turn ends asking the user for the request.
3. Dispatch `plan-reviewer` via `invoke_subagent`, and in the same turn output the verbatim prompt sent to it inside a blockquote (`>`):
   - **TypeName**: `plan-reviewer`
   - **Role**: `Plan Reviewer`
   - **Prompt**:
     ```markdown
     Review the implementation plan at <plan-link>.

     ### Request
     <the request from step 2>
     ```

   `<plan-link>` is the absolute `file://` path of the plan. The prompt carries only the plan and the request; the subagent's definition carries the whole protocol.

   *Completion criterion*: `plan-reviewer` is dispatched and the conversation contains the verbatim dispatched prompt inside a blockquote (`>`).
4. **Challenge & Adjudicate Findings**:
   When the subagent replies, read `plan_review.md` in full with `view_file` and verify each finding against the codebase (`file:line`) and the request before editing the plan:
   - **Holds**: Confirmed by code evidence (`file:line`) or the request. Apply the remediation to `implementation_plan.md`.
   - **Fails**: Contradicted by code evidence or the request. Keep `implementation_plan.md` as it is and record the refuting `file:line` or request text.
   - **Partly holds**: Apply only the confirmed part to `implementation_plan.md`, and keep the rest with its refuting evidence.

   For each finding that **Holds** or **Partly holds**, classify the remediation actually applied to `implementation_plan.md`:
   - **`Design revision`**: the applied fix replaces a decision the plan made about how the system works or is built with a new design choice.
   - **`Fact alignment`**: the applied fix leaves every decision the plan made intact and only brings the plan into agreement with a fact already fixed in the codebase or in a decision the plan already settled.

   *Completion criterion*: every finding in `plan_review.md` is judged as Holds, Fails, or Partly holds against the codebase and request; every confirmed change is written into `implementation_plan.md`; and every applied remediation is classified as `Design revision` or `Fact alignment`.
5. **Present Adjudication**:
   Report the adjudication to the user in a single pass:
   - Link to `plan_review.md` (with its overall verdict) and `implementation_plan.md` (with line links to each remediation).
   - **Holds / Partly holds — Design revisions**: For each applied `Design revision`, explain the redesign in full so the user can judge it directly:
     1. **Context**: what business flow or user job this part serves, what it does in that flow, and where it sits in the code (`file:line` and boundary), so the user understands what it does and where it lives on the first read.
     2. **Original plan intent**: what the plan expected that part to accomplish when it was drafted.
     3. **Reviewer's rejection**: how `plan-reviewer` rejected the proposal in the plan.
     4. **Why the rejection holds**: why that rejection is sound against the codebase (`file:line`) and the request.
     5. **New design resolution**: how the new solution written into `implementation_plan.md` achieves the valid original intent while eliminating the flaw `plan-reviewer` exposed.
   - **Holds / Partly holds — Fact alignments**: For each applied `Fact alignment`, state the finding and the exact correction made to `implementation_plan.md` with its confirming `file:line`.
   - **Fails (and refuted parts of Partly holds)**: Each rejected finding with its full refutation rationale and `file:line` or request proof, flagged for potential user overrule.
   - **Open Questions**: Any open question from `plan_review.md`, with both readings presented for the user's decision.
   - Ask the user to confirm the updated plan (and any `Design revision` resolutions) or overrule any rejected findings.

   *Completion criterion*: the report links both artifacts, presents every `Design revision` with all five context-to-resolution items, lists every `Fact alignment` with its applied correction, lists every `Fails` finding (and refuted part) with refutation citations for user overrule, surfaces any `Open Questions`, and ends awaiting the user's decision.
