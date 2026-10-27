---
name: spawn-subagent
description: Delegate work to a subagent through a cold-read prompt that hands over the problem and leaves the solution to the subagent
disable-model-invocation: true
---

## 1. Frame the Prompt

Write the prompt so an engineer holding only the prompt can complete the work without asking anything back, dropping orchestration words about delegating. Replace every **reference** — a pointer to a specific item the conversation already pinned down — with that item's full content and location. Carry over every **category** — a set whose members the work must find or act on — in the user's own words with where its members live, without listing members you found yourself (listing members you found claims completeness and makes the subagent stop at the list's edge; **When** the user named the members, their list is the category and enters verbatim).

In `### Role`, state the subagent's expertise and what counts as a successful outcome for its run; **When** the task evaluates a claim, plan, or implementation, state that success is proving where it fails rather than agreeing with the prompt.

In `### Problem`, state only **settled** facts — observations with their exact locations and user decisions that stay true whatever the subagent finds — never your conclusions from them or constraints you invented. **When** the work evaluates a hypothesis, plan, or implementation, state it as an open claim under judgment rather than a settled verdict.

In `### Objective`, state the required end-state and every question or acceptance condition the deliverable must satisfy in a form verifiable from the subagent's output alone, without prescribing the execution steps or technical solution the subagent must use to reach it.

In `### Scope`, state the boundary of the subagent's work: which components, directories, or architectural layers it covers (carrying over any category as defined above rather than pre-filtering into a partial file list) and which adjacent areas or mutations are out of bounds.

- **Completion Criterion**: The prompt passes the cold read with every reference expanded and every category preserved unenumerated; `### Role` defines success for the run; `### Problem` contains only settled facts and open claims under judgment; `### Objective` states verifiable acceptance conditions without prescribing the solution; and `### Scope` states both covered targets and out-of-bounds areas or mutations.

---

## 2. Dispatch

Call `invoke_subagent` with `TypeName`: `self`, `Model`: `inherit`, and `Prompt` formatted as:

```markdown
### Role
<From Step 1>

### Problem
<From Step 1>

### Objective
<From Step 1>

### Scope
<From Step 1>

### Delivery
1. Write the full result to `<appDataDir>/brain/<your-conversation-id>/<artifact>.md`.
2. Reply with only: Completed: <artifact>.md written to <appDataDir>/brain/<your-conversation-id>/<artifact>.md
```

- **Completion Criterion**: `invoke_subagent` is dispatched with `TypeName: "self"`, `Model: "inherit"`, and all five prompt sections (`Role`, `Problem`, `Objective`, `Scope`, `Delivery`) populated.

---

## 3. Surface Dispatched Prompt

Immediately after calling `invoke_subagent`, output the verbatim `Prompt` into the conversation inside a blockquote (`>`).

- **Completion Criterion**: The conversation contains the verbatim `Prompt` sent to `invoke_subagent` inside a blockquote (`>`).

---

## 4. Receive & Follow Up

1. When the subagent replies, read `<appDataDir>/brain/<your-conversation-id>/<artifact>.md` in full with `read_file`, and leave the subagent in idle state without calling `manage_subagents` to kill it. Do not call `send_message` to follow up unless the user requests a follow-up.
2. **When** the user requests a follow-up with the subagent, call `send_message` with only the new directive framed by Step 1, opening with the `### Delivery` block from Step 2 and pointing to the subagent's prior findings by their identifiers.

- **Completion Criterion**: `<artifact>.md` is read in full with `read_file`, the subagent remains unkilled, and `send_message` is called only when requested by the user.
