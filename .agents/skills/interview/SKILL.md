---
name: interview
description: Align user and agent understanding into a verified specification before acting
disable-model-invocation: true
---

## Step 1: Workspace Grounding & Gap Trace

Before each round of questions, inspect the workspace material in the currently active scope and trace each step required to achieve the outcome and what happens when any condition that step relies on fails, deferring branches behind an unanswered fork until the user picks that branch.

For each point in this trace, test whether it is **settled**—meaning the user's words and the workspace are mutually consistent at that point and rule out every alternative outcome:

- **When** a point the user left unsaid is **settled** by the workspace, record it with its workspace citation as an **Assumption** for Step 3.
- **When** a point is **unsettled**, turn it into a question for Step 2 with candidate resolutions grounded in the workspace.

*Completion criterion*: Every step and failure condition in the active scope has been traced against the workspace, every unsaid point settled by the workspace is recorded as a cited Assumption, and every unsettled point is framed as a question with workspace-grounded candidate resolutions.

## Step 2: Dependency-Ordered Question Rounds

**When** Step 1 produces one or more questions, call `ask_question`:

- **Batching**: Include every unsettled question that is independent of all other unsettled questions, holding any question that depends on an unanswered upstream choice until the next round.
- **Question context**: In each `question`, state the finding from Step 1 that leaves the point unsettled.
- **Option framing**: Format each option as `<Decision> — <Resulting consequence>`, placing `(Recommended)` first on the option best supported by the established context.

**When** the user answers a round, return to Step 1 to trace the updated scope until Step 1 produces zero unsettled points.

*Completion criterion*: Zero unsettled points remain across all chosen branches.

## Step 3: Playback Gate

**When** zero unsettled points remain, call `ask_question` (`is_multi_select: true`) to present the complete specification (all locked decisions and workspace Assumptions):

- `question`: The full specification, with each decision and cited Assumption stated as a distinct item.
- `options`:
  - `"(Recommended) Confirmed — the specification matches my intent"`
  - One `"Revise: <item>"` option per item in the specification.

- **When** the user selects any item to revise, treat the selected items and their dependents as unsettled, return to Step 1, and re-issue the Playback Gate once settled.
- **When** the user confirms with no revisions, output the confirmed specification in the chat response and end the interview.

*Completion criterion*: The user has confirmed the specification in `ask_question` with no revisions selected, and the final specification is output in the conversation.
