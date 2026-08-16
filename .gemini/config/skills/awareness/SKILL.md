---
name: awareness
description: write goal.md and run the verification loop.
disable-model-invocation: true
---

# Awareness Skill

Apply this skill to every non-trivial user request. 

## Trivial vs Non-Trivial
Skip this skill ONLY IF the request meets ALL these conditions:
- Single-file change
- Codebase exploration to answer a question only
- No logic change (typo fix, comment, formatting, config swap, simple rename)
- No new behavior introduced

Everything else is non-trivial. Execute the following workflow.

---

## Workflow

### Phase 1: Definition
1. Analyze the user request. 
2. If codebase exploration is needed, state what you will do next and start your work.
3. Define functional requirements, non-functional requirements, and user outcomes.
4. Write these to `./.gtd/<task_name>/goal.md`. Do not commit this file.
5. **stop execution.** Show the content of `goal.md` to the user and wait for their explicit approval. Do not write code.

#### goal.md Format
```markdown
# <Task Name>

## Context
<What area of the codebase is affected. What the existing code does. Why this change is needed.>

## User Outcomes
- After this task, user should be able to <do something specific>
- After this task, user should see <specific observable result>

## Functional Requirements
- [ ] <verifiable constraint>
- [ ] <verifiable constraint>

## Non-Functional Requirements
- [ ] <verifiable constraint>
- [ ] <verifiable constraint>
```

### Phase 2: Execution
(Start this phase only after user approves goal.md)

1. **Check Base Branch:** Run `git branch --show-current` to identify the current branch. Store this name internally as `<base_branch>`. Skip this if the user explicitly provided the base branch name.
2. **Create Feature Branch:** Run `git checkout -b gtd/<task_name>`.
3. **Write Code:** Implement the exact requirements from `goal.md`.
4. **Strict Commit:** 
   - Run `git status`.
   - Run `git add <specific_file_path>` strictly for files you modified or created for this feature.
   - Run `git commit -m "<message>"`.
   - Constraint: Do not use `git commit -a` or `git add .`. Do not commit any files inside `./.gtd/`.

### Phase 3: Review Preparation
- **Clear Old Feedback and Generate Diff:** Run `rm -f ./.gtd/<task_name>/feedback.md && git diff <base_branch>...gtd/<task_name> > ./.gtd/<task_name>/diff.txt`.

### Phase 4: Subagent Delegation
Call a new subagent with the exact prompt below:

> You are a code reviewer. Evaluate if a code change satisfies its defined goal.
> 
> 1. Read `./.gtd/<task_name>/goal.md` (Context, Outcomes, Requirements).
> 2. Read `./.gtd/<task_name>/diff.txt` (The exact code changes).
> 3. Evaluate User Outcomes. If they fail, the entire change fails.
> 4. Evaluate each Functional and Non-Functional requirement against the diff. Check for bugs, logic errors, edge cases, or unnecessary complexity.
> 5. **Evaluate Architecture & Patterns.** You must strictly apply these definitions. **Any violation of these definitions is a blocking issue:**
>    - **Architecture - Minimalism:** Code must have low coupling. Flag any abstractions that do not solve a concrete problem. Favor monolithic design over microservices for non-massive codebases.
>    - **Architecture - Flexibility:** Code must allow adding new features or modifying existing ones with minimal to no changes to existing code (Open-Closed principle).
>    - **Pattern Analysis:** Identify the exact design patterns used in specific code blocks. Explain the problem each pattern attempts to solve. Evaluate if the pattern is appropriate locally and within the broader codebase context. Flag performance bottlenecks or anti-patterns created by how patterns interact.
> 6. Use `view_file` on files referenced in the diff if you need full context.
> 7. Write your review to `./.gtd/<task_name>/feedback.md`.
> 
> Your review file MUST end with exactly one of these lines:
> - `## Verdict: APPROVE` (All requirements met, architecture sound, no blocking issues)
> - `## Verdict: BLOCK` (Requirements missed, architecture violations found, or blocking issues found. List each issue with exact file and line references)

### Phase 5: Resolution
Read `./.gtd/<task_name>/feedback.md` after the subagent completes.

- If **APPROVE**: State "Review passed. Branch gtd/<task_name> is ready to merge." **stop here.** Wait for the user to handle the merge.
- If **BLOCK**: 
  1. Print the blocking issues to the user in chat. Let they know what is happening.
  2. Fix the issues on the `gtd/<task_name>` branch.
  3. Go back to **Phase 3** (Review Preparation) and repeat the loop.
