---
name: spawn-subagent
description: Delegate work to a subagent through a cold-read prompt that hands over the problem and leaves the solution to the subagent
disable-model-invocation: true
---

# CORE DIRECTIVE

A subagent knows nothing but its prompt, and it takes that prompt as both truth and map: it believes every assertion and searches only where the prompt points. Its value is what you have not already seen. You own the **Problem Space**; the subagent owns 100% of the **Solution Space**.

---

## 1. Frame the Problem

De-reference the conversation into a prompt that passes the **cold read**: an engineer holding only the prompt — no chat history, no thoughts, no git log — can start work without asking anything back. Every reference to this conversation is expanded into its full content; orchestration words about delegating are dropped.

Assert only what is **settled** — what stays true whatever the subagent finds. What you observed is settled; what you concluded from it is not. What the user decided is settled; a constraint you invented is not. When the task is to judge something, that thing enters the prompt as a claim under judgment, never as a verdict.

Draw the boundary of the problem without marking any spot inside it. Do NOT tell the subagent what you changed, where you looked, or which cases you already covered: that is your map, and it will follow it into your blind spot.

Give the subagent a role defined by what success means for it. When the outcome is a judgment, success is finding what is wrong — state it, because by default a subagent agrees with whoever asked.

- **Completion Criterion**: The prompt passes the cold read, and every sentence under `Problem` stays true whatever the subagent finds.

---

## 2. Dispatch

Invoke via `invoke_subagent` with `Model`: `inherit` and this `Prompt`:

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

1. Read the delivered artifact with `view_file`.
2. To follow up, `send_message` only the new directive, opening with the deliverable. The subagent still holds its own context: point to its prior findings by their identifier. The directive obeys Step 1 — settled facts, no map.
3. When no follow-up remains, terminate the subagent via `manage_subagents`.

- **Completion Criterion**: Result ingested and the subagent terminated.
