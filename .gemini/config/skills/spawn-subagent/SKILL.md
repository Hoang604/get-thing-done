---
name: spawn-subagent
description: Delegate work to a fresh subagent through a cold-read prompt that expands references in place and leaves the user's request intact
disable-model-invocation: true
---

## 1. Frame the Prompt

Write the task body from the user's message so an engineer holding only the prompt can complete the work without asking anything back, dropping orchestration words about delegating. Replace every **reference** — a pointer to a specific item the conversation already pinned down — in place with that item's full content and location. Carry over every **category** — a set whose members the work must find or act on — in the user's own words with where its members live, without listing members you found yourself (listing members you found claims completeness and makes the subagent stop at the list's edge; **when** the user named the members, their list is the category and enters verbatim). **When** and only when the user explicitly requests out-of-bounds areas or forbidden mutations, include an `### Out of Bounds` section stating those exact restrictions; otherwise omit `### Out of Bounds`. Check the drafted task body by deleting the user's words and the expanded references: if anything remains beyond pure connecting syntax, delete that added material.

- **Completion Criterion**: The task body passes the cold read with every reference expanded in place and every category preserved unenumerated in the user's own words, `### Out of Bounds` is included if and only if explicitly requested by the user, and deleting the user's words and expanded references from the task body leaves only pure connecting syntax.

---

## 2. Dispatch

Always call `invoke_subagent` to launch a new subagent with `TypeName`: `self` and `Model`: `inherit` (changing `invoke_subagent` parameters if and only if the user explicitly requests exact parameters), and `Prompt` formatted as:

```markdown
<From Step 1>

### Out of Bounds (include if and only if explicitly requested by the user)
<From Step 1>

### Delivery
1. Write the full result to `<appDataDir>/brain/<your-conversation-id>/<artifact>.md`.
2. Reply with only: Completed: <artifact>.md written to <appDataDir>/brain/<your-conversation-id>/<artifact>.md
```

- **Completion Criterion**: A new subagent is launched via `invoke_subagent` with `TypeName: "self"` and `Model: "inherit"` (or the exact parameters explicitly requested by the user) and `Prompt` containing the task body from Step 1, `### Out of Bounds` if and only if explicitly requested by the user, and `### Delivery`.

---

## 3. Surface Dispatched Prompt

Immediately after calling `invoke_subagent`, output the verbatim `Prompt` into the conversation inside a blockquote (`>`).

- **Completion Criterion**: The conversation contains the verbatim `Prompt` sent to `invoke_subagent` inside a blockquote (`>`).

---

## 4. Receive & Follow Up

1. When the subagent replies, read `<appDataDir>/brain/<your-conversation-id>/<artifact>.md` in full with `read_file`, and leave the subagent in idle state without calling `manage_subagents` to kill it. Do not call `send_message` to follow up unless the user requests a follow-up.
2. **When** the user requests a follow-up with an existing subagent, call `send_message` with only the new directive framed by Step 1, opening with the `### Delivery` block from Step 2 and pointing to the subagent's prior findings by their identifiers.

- **Completion Criterion**: `<artifact>.md` is read in full with `read_file`, the subagent remains unkilled, and `send_message` is called only when requested by the user.
