---
name: awareness
description: user manually trigger. After trigger, follow forever. Do not trigger the skill yourself.
---

# Awareness Skill — Self-Review Loop

Once activated, this skill applies to **every non-trivial user request** for the rest of the conversation. Do not selectively skip it. If the context compacted, you must stop and inform user.

## What Counts as Non-Trivial

A request is **trivial** (skip this skill) if it meets ALL of:
- Single-file change
- Explore codebase to answer question
- No logic change (typo fix, comment, formatting, config value swap, simple rename)
- No new behavior introduced

Everything else is **non-trivial** — use this skill.

---

## Flow

### 1. Define Goal

Before any code change:

1. Analyze the user request to understand it. 
- If you need to explore the codebase to gather context, you must state: "I am exploring the codebase to understand the request."
- State your understanding of the request back to user.
- Stop and wait for user confirmation. Start work only on approval.
2. Identify **functional requirements** (what must the code do) and **non-functional requirements** (performance, style consistency, no regressions, edge cases). Write these as concrete, verifiable constraints — not vague descriptions.
3. Identify **user outcomes** — what the user should be able to do or see after the task is done. Keep these high-level and outcome-focused, not implementation-detailed.
4. **Show the goal to the user in chat first.** Wait for approval.
5. After approval, write to `./.gtd/<task_name>/goal.md`.

`<task_name>` = short kebab-case name describing the feature (e.g., `add-user-auth`, `fix-pagination-bug`).

#### goal.md Format

This file must be **fully self-contained**. A reader with zero context about the conversation or codebase must understand what is being built and why. Do not use references like "the feature we discussed" or "as requested".

```markdown
# <Task Name>

## Context
<What area of the codebase is affected. What the existing code does.
Why this change is needed. Enough background that a stranger can understand.>

## User Outcomes
- After this task, user should be able to <do something specific>
- After this task, user should see <specific observable result>

## Functional Requirements
<Each requirement states what must be true, not how to make it true.
Do not dictate implementation — verify outcomes.>
- [ ] <verifiable constraint>
- [ ] <verifiable constraint>

## Non-Functional Requirements
- [ ] <verifiable constraint>
- [ ] <verifiable constraint>
```

### 2. Create Branch

First run `git branch` to check where you currently is, then create new branch

```bash
git checkout -b gtd/<task_name>
```

Branch from whatever branch is currently checked out.

### 3. Do the Work

Implement the feature/fix on `gtd/<task_name>` branch. Commit as normal.

### 4. Prepare Review Materials

Before delegating, the **main agent** must commit only the specific files it modified or created during this turn (do not commit other uncommitted files changed by the user or other agents, and do not commit the `goal.md` or `diff.txt` files). Then, run: `git diff <original_branch>...gtd/<task_name> > ./.gtd/<task_name>/diff.txt`

This is necessary because the triple-dot diff compares committed changes, and subagents cannot run terminal commands.

### 5. Request Review via Subagent

Delegate a **new self subagent** with this task:

> You are a code reviewer. Your job is to evaluate whether a code change satisfies its defined goal.
>
> **CRITICAL**: Do NOT read or look at any previous round feedback files (`./.gtd/<task_name>/feedback/round-*.md`). This must be a completely independent, blind review to ensure an unbiased evaluation of the changes from scratch.
>
> 1. Read `./.gtd/<task_name>/goal.md` — this contains the context, user outcomes, functional and non-functional requirements.
> 2. Read `./.gtd/<task_name>/diff.txt` — this contains the full code diff.
> 3. Evaluate the **User Outcomes** first. These are the high-level sanity check — does the change actually deliver what the user needs? If user outcomes are not met, the change fails regardless of FR/NFR status.
> 4. Evaluate each requirement in goal.md against the diff. Check:
>    - Does the code actually fulfill each functional requirement?
>    - Does the code satisfy each non-functional requirement?
>    - Are there obvious bugs, logic errors, or missed edge cases?
>    - Is the code unnecessarily complex for what it does?
> 5. If you need to read full source files for more context, use view_file on the relevant files referenced in the diff.
> 6. Write your review to `./.gtd/<task_name>/feedback/round-<N>.md` where N is the review round number (start at 1).
>
> Your review file MUST end with exactly one of:
> - `## Verdict: APPROVE` — all requirements met, no blocking issues.
> - `## Verdict: BLOCK` — one or more requirements not met, or blocking issues found.
>
> If BLOCK, list each blocking issue with specific file and line references.

### 6. Process Feedback

After subagent completes:

1. Read `./.gtd/<task_name>/feedback/round-<N>.md`.
2. If **APPROVE** → tell the user: "Review passed. Branch `gtd/<task_name>` is ready to merge." Let user handle the merge.
3. If **BLOCK** → report the blocking issues clearly in chat to the user first. Then, fix the identified issues on the same branch, and go back to **Step 4** (regenerate diff.txt) → **Step 5** (new subagent, increment round number).

### 7. Loop

Repeat steps 4–6 until verdict is APPROVE.

---

## Rules

- **Never merge automatically.** Only inform user the branch is ready.
- **Each review round uses a new subagent.** Do not reuse subagent context — fresh eyes each round.
- **Do not skip the goal definition step.** Even if you think you understand the request, write it down and show the user.
- **Do not modify goal.md after initial approval** unless the user explicitly changes requirements.
- **Do not commit goal.md or diff.txt.** These files must remain untracked in the workspace so they do not pollute the git diff.
- **State exploration intent clearly.** If exploring the codebase to understand a request, always state this intent first and wait for confirmation with your stated understanding before proceeding to goal definition or work.
- **Blind reviews to prevent bias.** Subagents evaluating round N must not read or be influenced by feedback from previous rounds (1 to N-1). Every review round must be a completely fresh, independent, blind assessment of the current diff against the goal.
