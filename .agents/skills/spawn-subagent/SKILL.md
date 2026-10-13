---
name: spawn-subagent
description: Delegate work to a subagent through a cold-read prompt that hands over the problem and leaves the solution to the subagent
disable-model-invocation: true
---

# CORE DIRECTIVE

A subagent knows nothing but its prompt, and it takes that prompt as both truth and map: it believes every assertion and searches only where the prompt points. Its value is what you have not already seen. You own the **Problem Space**; the subagent owns 100% of the **Solution Space**.

---

## 1. Frame the Problem

De-reference the conversation into a prompt that passes the **cold read**: an engineer holding only the prompt — no chat history, no thoughts, no git log — can start work without asking anything back. A **reference** points at one thing the conversation already pinned down: replace it with its full content. A **category** names a set whose members the work must find or act on: carry it over in the user's own words, with where its members live. Orchestration words about delegating are dropped.

Assert only what is **settled** — what stays true whatever the subagent finds. What you observed is settled; what you concluded from it is not. What the user decided is settled; a constraint you invented is not. When the task is to judge something, that thing enters the prompt as a claim under judgment, never as a verdict.

The subagent finds every member of a category itself; its value is the members you missed. A list of members you found claims completeness without stating it — a conclusion, not an observation — and the subagent searches that list and stops at its edge. When the user named the members, their list is the category: carry it over verbatim.

Give the subagent a role defined by what success means for it. When the outcome is a judgment, success is finding what is wrong — state it, because by default a subagent agrees with whoever asked.

- **Completion Criterion**: The prompt passes the cold read, and every sentence under `Problem` stays true whatever the subagent finds.

---

## 2. Dispatch

Invoke via `invoke_subagent` with `Model`: `inherit`, always `self` subagent when using this skill, and this `Prompt`:

```markdown
### Role
<Role, defined by what success means for it>

### Problem
<Settled facts only; the subject under judgment stated as a claim>

### Objective
<End-state as behavior an outsider can check, by the user's own standard of success>

### Scope
<Boundary of the work you assign; omit this section when the whole system is in scope>

### Delivery
<Exactly one of the two blocks below>
```

Delivery — write-capable subagent with a deliverable longer than a short answer (its tools create artifacts only in its own directory, hence the copy):

```markdown
1. Write the full result to `<artifact>.md` in your own artifact directory.
2. Copy it: cp "<your artifact directory>/<artifact>.md" "<appDataDir>/brain/<parent-conversation-id>/<artifact>.md"
3. Reply with only: Completed: <artifact>.md delivered
```

Delivery — read-only subagent, or a short answer:

```markdown
Reply with the result directly.
```

- **Completion Criterion**: `invoke_subagent` dispatched; every section carries content, and only `Scope` may be absent.

---

## 3. Receive & Follow Up

1. When the subagent delivered an artifact, read it in full with `view_file`; when it replied directly, its reply is the result.
2. To follow up, `send_message` only the new directive, opening with the deliverable. The subagent still holds its own context: point to its prior findings by their identifier. The directive obeys Step 1 — settled facts, categories carried over whole.
3. When no follow-up remains, keep the agent idle so it can take a later follow-up.

- **Completion Criterion**: The result is read in full and meets every point of the prompt's `Objective`; each point it misses has a follow-up sent for it.
