---
name: interview
description: Align user and agent understanding into a verified specification before acting
disable-model-invocation: true
---

## Step 1: Workspace Grounding & Gap Trace

Before calling `ask_question` in any round, inspect the workspace material governing the active path not yet settled in an earlier round and emit in the chat response an itemized trace listing, as separate items, each execution step required to reach the outcome and each failure of a condition that step relies on, stopping each branch at any fork where multiple downstream paths remain consistent with the user's words and the workspace until the user's answer selects a path.

In that emitted trace, rule on each item individually while holding all other items fixed, citing the governing `path:line` (or verified workspace absence) and user statement: classify an item as **settled** when the user's words and the workspace are mutually consistent at that item and rule out every alternative outcome—marking it as a **locked decision** when stated by the user or as a cited **Assumption** when left unsaid by the user—and otherwise classify it as **unsettled** with the specific conflict or open alternative found.

*Completion criterion*: The chat response contains an individual cited ruling (`locked decision`, `Assumption`, or `unsettled`) for every execution step and failure condition along the active path not yet settled in an earlier round, up to any fork where multiple downstream paths remain consistent with the user's words and the workspace.

## Step 2: Dependency-Ordered Question Rounds

**When** one or more items are **unsettled**, before calling `ask_question`, state in chat for each **unsettled** item individually (holding the other items fixed) whether another currently **unsettled** item's answer can eliminate this item or change its candidate resolutions—marking it **hold** (citing that upstream **unsettled** item) when so, and **ask now** otherwise—and include in `ask_question` strictly every item marked **ask now**.

For each **ask now** item, before calling `ask_question`, list in chat the distinct candidate resolutions that settle the item without contradicting settled items and, for each candidate individually (holding the other candidates fixed), state what it reuses, modifies, or adds in the workspace (`path:line` where existing material applies) and the resulting consequence on behavior.

For each candidate of an **ask now** item individually (holding the other candidates fixed), state in chat before calling `ask_question` any cited user statement or workspace convention (`path:line`) that aligns with it; mark one candidate **recommended** when cited context aligns with it and every competing candidate diverges from that cited context without countervailing cited support, and otherwise mark **none recommended**.

Call `ask_question` constructed strictly from those emitted rulings:

- **Question context**: In each `question`, state the finding from Step 1 that leaves the item **unsettled**.
- **Option framing**: Format each option as `<Decision> — <Resulting consequence>` from its emitted candidate ruling, placing `(Recommended)` first on the option marked **recommended** and omitting `(Recommended)` when marked **none recommended**.

**When** the user answers a round, record each answer as a **locked decision** and return to Step 1 to trace the updated active path until Step 1 produces zero **unsettled** items.

*Completion criterion*: In every round with **unsettled** items, the chat response before `ask_question` rules on every **unsettled** item (`hold` citing an upstream **unsettled** item, or `ask now` with individual workspace, consequence, and recommendation rulings for each candidate), `ask_question` contains strictly the **ask now** items constructed from those rulings, and rounds repeat until zero **unsettled** items remain across all chosen paths.

## Step 3: Playback Gate

**When** zero **unsettled** items remain, call `ask_question` (`is_multi_select: true`) to present the complete specification (all **locked decisions** and cited workspace **Assumptions** emitted across rounds):

- `question`: The full specification, with each decision and cited Assumption stated as a distinct item.
- `options`:
  - `"(Recommended) Confirmed — the specification matches my intent"`
  - One `"Revise: <item>"` option per item in the specification.

- **When** the user selects any `"Revise: <item>"` option, before calling `ask_question` again, emit in chat an individual ruling for each remaining item in the specification (holding the other items fixed) stating whether its settlement or candidate resolutions relied on any selected revised item—marking it **unsettled** (citing that revised item) when so and **retained** otherwise—then return to Step 1 with the selected items and dependent items marked **unsettled**, and re-issue the Playback Gate once zero **unsettled** items remain.
- **When** the user confirms with no revisions, output the confirmed specification in the chat response and end the interview.

*Completion criterion*: Every Playback Gate `ask_question` presents every accumulated **locked decision** and cited **Assumption**, every revision round emits in chat an individual **unsettled** or **retained** ruling for each remaining item before re-tracing, and the user has confirmed the specification in `ask_question` with no revisions selected with the final specification output in the conversation.
