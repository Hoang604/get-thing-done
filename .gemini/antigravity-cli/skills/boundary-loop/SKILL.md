---
name: boundary-loop
description: Orchestrate an N-iteration fresh-context boundary refinement loop by drafting a cold-read task specification for user confirmation and sequentially invoking fresh boundary-worker subagents until convergence or iteration cap
disable-model-invocation: true
---

## 1. Draft & Confirm the Cold-Read Task (`task.md`)

Write `<appDataDir>/brain/<your-conversation-id>/task.md` so an engineer holding only `task.md` and the workspace can complete the work without asking anything back, dropping orchestration words about delegating or looping. Replace every **reference** — a pointer to a specific item the conversation already pinned down — with that item's full content and location. Carry over every **category** — a set whose members the work must find or act on — in the user's own words with where its members live, without listing members you found yourself (listing members you found claims completeness and makes the subagent stop at the list's edge; **When** the user named the members, their list is the category and enters verbatim).

In `### Problem`, state only **settled** facts — observations with their exact locations and user decisions that stay true whatever the subagent finds — never your conclusions from them or constraints you invented. **When** the work evaluates a hypothesis, plan, or implementation, state it as an open claim under judgment rather than a settled verdict.

In `### Objective`, state the required end-state and every question or acceptance condition the deliverable must satisfy in a form verifiable from the subagent's output alone, without prescribing the execution steps or technical solution the subagent must use to reach it.

In `### Scope`, state the boundary of the subagent's work: which components, directories, or architectural layers it covers (carrying over any category as defined above rather than pre-filtering into a partial file list) and which adjacent areas or mutations are out of bounds.

Format `<appDataDir>/brain/<your-conversation-id>/task.md` as:

```markdown
### Problem
<From Step 1>

### Objective
<From Step 1>

### Scope
<From Step 1>
```

Extract the iteration cap $N$ from the user's request (**When** the user does not specify $N$, set $N = 3$).

Output the clickable link `[task.md](file://<appDataDir>/brain/<your-conversation-id>/task.md)`, the iteration cap $N$, and the verbatim contents of `task.md` inside a blockquote (`>`), then stop and wait for the user's confirmation before starting the loop. **When** the user requests changes to the task or to $N$, update `<appDataDir>/brain/<your-conversation-id>/task.md` accordingly, output the updated `task.md` verbatim inside a blockquote (`>`), and wait for confirmation again.

- **Completion Criterion**: `<appDataDir>/brain/<your-conversation-id>/task.md` exists on disk and passes the cold read with every reference expanded and every category preserved unenumerated; `### Problem` contains only settled facts and open claims under judgment; `### Objective` states verifiable acceptance conditions without prescribing the solution; `### Scope` states both covered targets and out-of-bounds areas or mutations; `task.md` and $N$ have been shown verbatim to the user; every revision requested by the user has been written to `task.md`; and the user has confirmed to start the loop.

---

## 2. Execute the Sequential Fresh-Context Loop ($i = 1 \dots N$)

Once the user confirms Step 1, run passes sequentially from $i = 1$ to $N$. In each pass $i$:

1. **Dispatch Fresh Worker**: Call `invoke_subagent` with a **new** subagent instance (`TypeName`: `boundary-worker`, `Model`: `inherit`, `Role`: `Boundary Worker (Pass <i>/<N>)`), passing only the path to `task.md` and never any prior pass's `boundary_plan.md` or summary:
   ```markdown
   ### Task File
   <appDataDir>/brain/<your-conversation-id>/task.md
   ```

2. **Evaluate Pass Outcome**: When the `boundary-worker` for pass $i$ replies:
   - **When** the reply begins with `CONVERGED:` or `BLOCKED:`, or when $i = N$: stop the loop immediately without spawning another pass, and report to the user:
     - the stop reason (`CONVERGED` at pass $i$, `BLOCKED` at pass $i$, or reached max passes $N$),
     - the clickable link `[boundary_plan.md](file://...)` for each executed pass $1 \dots i$, and
     - the baseline check result from the final completed pass.
   - **When** the reply begins with `COMPLETED:` and $i < N$: do not read pass $i$'s `boundary_plan.md` into your context; output a one-line progress note with the clickable link to pass $i$'s `boundary_plan.md` and immediately dispatch a new `boundary-worker` instance for pass $i + 1$.

- **Completion Criterion**: Every dispatched pass used a brand-new `boundary-worker` instance receiving only `task.md`, no prior pass's `boundary_plan.md` was read into parent context or forwarded to a subsequent pass, the loop terminated upon `CONVERGED:`, `BLOCKED:`, or pass $N$, and all executed passes' `[boundary_plan.md](file://...)` links were reported to the user.
