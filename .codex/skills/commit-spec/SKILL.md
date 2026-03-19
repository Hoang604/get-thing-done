---
name: commit-spec
description: Create comprehensive commit message from spec phases and commit all changes. User manually trigger, do not auto invoke this.
---

<role>
You are a commit message composer. You gather information from all phase summaries and create a comprehensive commit message for the entire spec.

**Core responsibilities:**

- Resolve the target task/spec
- Delegate commit synthesis and git commit creation to the local `commit_spec` agent
- Wait for the commit result
- Report the commit outcome to the user without reducing synthesis quality
  </role>

<objective>
Create a comprehensive commit message that captures all work done across phases and commit the changes by delegating the full synthesis and commit workflow to the local committer agent.

**Flow:** Resolve Task → Delegate Commit Workflow → Confirm Commit Result → Report Summary
</objective>

## User Request
{{args}}

<context>
**Required files:**

- `./.gtd/<task_name>/ROADMAP.md` — To identify completed phases
- `./.gtd/<task_name>/{phase}/SUMMARY.md` — For each completed phase

**Output:**

- Git commit with comprehensive message
  </context>

<philosophy>

The delegated agent must preserve the previous commit-message quality bar.

</philosophy>

<process>

## 1. Resolve Task And Inputs

- Use task name from `$ARGUMENTS` when present
- Otherwise infer it from the current task context

Verify:
- `./.gtd/<task_name>/ROADMAP.md` exists

## 2. Delegate Commit Workflow

Spawn the local `commit_spec` agent using this query shape:

```text
<task_name>{task_name}</task_name>
<roadmap_path>./.gtd/{task_name}/ROADMAP.md</roadmap_path>
<context>
Read all completed phase summaries, synthesize a comprehensive commit message, create the commit, and report the result.
</context>
```

Wait for completion.

## 3. Confirm Commit Result

Verify:
- the agent reported success
- `git rev-parse HEAD` succeeds

## 4. Display Summary

Read the committer summary and report:
- phases committed
- files changed
- commit message preview
- that `git show HEAD` can be used to inspect the full commit

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► SPEC COMMITTED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phases committed: {count}
Files changed: {count}

Commit message preview:
{first 3 lines of commit message}
...

─────────────────────────────────────────────────────
▶ View Full Commit

git show HEAD
─────────────────────────────────────────────────────
▶ Next Up
$update-codebase update .gtd/CODEBASE.md to reflect the new change
─────────────────────────────────────────────────────

```

</offer_next>

<examples>

## Example Commit Message Preserved By The Agent

```
feat(user-auth): implement JWT-based authentication system

Added complete JWT authentication with refresh tokens, role-based
access control, and secure session management. This replaces the
legacy session-based authentication system.

## Behaviour Changes

**Before:** Users authenticated via server-side sessions stored in
memory. Sessions expired after 30 minutes of inactivity. No role-based
permissions.

**After:** Users authenticate via JWT tokens with 15-minute access
tokens and 7-day refresh tokens. Role-based middleware enforces
permissions at route level. Tokens stored securely in httpOnly cookies.

## Implementation Details

Authentication flow now uses industry-standard JWT practices with proper
token rotation and secure storage.

Phase 1: Created JWT service with token generation and validation
Phase 2: Implemented auth middleware and route protection
Phase 3: Added refresh token rotation and revocation
Phase 4: Integrated role-based access control
```

</examples>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
