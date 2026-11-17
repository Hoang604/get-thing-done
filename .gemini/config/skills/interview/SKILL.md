---
name: interview
description: Read before acting or asking the user clarifying questions whenever a request is underspecified, leaves multiple valid paths open, or conflicts with the workspace, or when the user asks for an interview.
---

## Scratch File & Chat Output

Record all Step 1 traces, Step 2 dependency/candidate rulings, and user answers cumulatively in a single scratch file at `<Artifact Directory>/scratch/interview-<id>.md` when `<Artifact Directory>` is provided (or `/tmp/interview-<id>.md` outside Antigravity), carrying forward every settled **locked decision** and cited **Assumption** across rounds and leaving the scratch file in place after Step 3. **When** executing Step 1 or Step 2 across any number of tool turns, emit Step 1–2 reasoning strictly into the scratch file and deliver only `ask_question` prompts in the conversation until Step 3 outputs the final specification—emitting at most one tool-expectation sentence before a read turn only when a governing workspace rule requires it. Never create scratch files inside the repository workspace, never omit Step 1–2 per-item rulings from the scratch file, and never echo Step 1 traces, Step 2 analyses, or intermediate code findings into chat.

## Step 1: Workspace Grounding & Gap Trace

In any round before calling `ask_question` or advancing to Step 3, inspect the workspace material governing the active path not yet settled in an earlier round and record in the scratch file an itemized trace listing, as separate items, each execution step required to reach the outcome and each failure of a condition that step relies on, stopping each branch at any fork where multiple downstream paths remain consistent with the user's words and the workspace until the user's answer selects a path.

In that scratch-file trace, rule on each item individually while holding all other items fixed, citing the governing `path:line` (or verified workspace absence) and user statement: classify an item as **settled** when the user's words and the workspace are mutually consistent at that item and rule out every alternative outcome—marking it as a **locked decision** when stated by the user or as a cited **Assumption** when left unsaid by the user—and otherwise classify it as **unsettled** with the specific conflict or open alternative found.

*Completion criterion*: The scratch file contains an individual cited ruling (`locked decision`, `Assumption`, or `unsettled`) for every execution step and failure condition along the active path not yet settled in an earlier round, up to any fork where multiple downstream paths remain consistent with the user's words and the workspace.

## Step 2: Dependency-Ordered Question Rounds

**When** one or more items are **unsettled**, before calling `ask_question`, record in the scratch file for each **unsettled** item individually (holding the other items fixed) whether another currently **unsettled** item's answer can eliminate this item or change its candidate resolutions—marking it **hold** (citing that upstream **unsettled** item) when so, and **ask now** otherwise—and include in `ask_question` strictly every item marked **ask now**.

For each **ask now** item, before calling `ask_question`, record in the scratch file the distinct candidate resolutions that settle the item without contradicting settled items, identify which settled **Assumption**s from the scratch file each **ask now** item's finding or candidate options depend on, and for each candidate individually (holding the other candidates fixed), state what it reuses, modifies, or adds in the workspace (`path:line` where existing material applies) and the resulting consequence on behavior.

For each candidate of an **ask now** item individually (holding the other candidates fixed), record in the scratch file before calling `ask_question` any cited user statement or workspace convention (`path:line`) that aligns with it; mark one candidate **recommended** when cited context aligns with it and every competing candidate diverges from that cited context without countervailing cited support, and otherwise mark **none recommended**.

Call `ask_question` constructed strictly from those scratch-file rulings:

- **Question context**: In each `question`, state the finding from Step 1 that leaves the item **unsettled** alongside a concise summary of only the settled **Assumption**s marked in the scratch file as relied on by that item's finding or candidate options; omit unrelated **Assumption**s and already **locked decision**s.
- **Option framing**: Format each option as `<Decision> — <Resulting consequence>` from its scratch-file candidate ruling, placing `(Recommended)` first on the option marked **recommended** and omitting `(Recommended)` when marked **none recommended**.

**When** the user answers a round, record each answer as a **locked decision** in the scratch file and return to Step 1 to trace the updated active path (carrying forward all settled rulings from earlier rounds) until Step 1 produces zero **unsettled** items.

*Completion criterion*: In every round with **unsettled** items, the scratch file before `ask_question` rules on every **unsettled** item (`hold` citing an upstream **unsettled** item, or `ask now` with relied-on **Assumption** markings and individual workspace, consequence, and recommendation rulings for each candidate), `ask_question` contains strictly the **ask now** items constructed from those rulings, and rounds repeat until zero **unsettled** items remain across all chosen paths.

## Step 3: Playback

**When** zero **unsettled** items remain, do not call `ask_question`; output the complete specification directly in the chat response—stating every accumulated **locked decision** and cited workspace **Assumption** recorded in the scratch file across rounds as a distinct item—and end the interview.

*Completion criterion*: Zero **unsettled** items remain, and the chat response directly outputs the complete specification containing every accumulated **locked decision** and cited **Assumption** as distinct items without issuing another `ask_question`.
