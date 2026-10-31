---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
disable-model-invocation: true
---

# Using Git Worktrees

## Overview

Ensure work happens in an isolated workspace. Prefer your platform's native worktree tools. Fall back to manual git worktrees only when no native tool is available.

**Core principle:** Detect existing isolation first. Then use native tools. Then fall back to git. Never fight the harness.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Step 0: Detect Existing Isolation

**Before creating anything, check if you are already in an isolated workspace.**

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are already in a linked worktree. Skip to Step 2 (Project Setup). Do NOT create another worktree.

Report with branch state:
- On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
- Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."

**If `GIT_DIR == GIT_COMMON` (or in a submodule):** You are in a normal repo checkout.

Has the user already indicated their worktree preference in your instructions? If not, ask for consent before creating a worktree:

> "Would you like me to set up an isolated worktree? It protects your current branch from changes."

Honor any existing declared preference without asking. If the user declines consent, work in place and skip to Step 2.

## Step 1: Create Isolated Workspace

**You have two mechanisms. Try them in this order.**

### 1a. Native Worktree Tools (preferred)

The user has asked for an isolated workspace (Step 0 consent). Do you already have a way to create a worktree? It might be a tool with a name like `EnterWorktree`, `WorktreeCreate`, a `/worktree` command, or a `--worktree` flag. If you do, use it and skip to Step 2.

Native tools handle directory placement, branch creation, and cleanup automatically. Using `git worktree add` when you have a native tool creates phantom state your harness can't see or manage.

Only proceed to Step 1b if you have no native worktree tool available.

### 1b. Git Worktree Fallback

**Only use this if Step 1a does not apply** — you have no native worktree tool available. Create a worktree manually using git.

#### Directory Selection, `.gitignore` Verification & Worktree Creation (Single-Turn Execution)

Follow this directory priority order (explicit user preference always beats observed filesystem state):
1. User-declared worktree directory preference in instructions.
2. Existing `.worktrees` (preferred) or `worktrees` directory at project root.
3. Default to `.worktrees` at project root.

**Execute directory selection, `.gitignore` verification/commit, and `git worktree add` in a single `run_command` call within one turn:**

```bash
LOCATION=$(if [ -d .worktrees ]; then echo ".worktrees"; elif [ -d worktrees ]; then echo "worktrees"; else echo ".worktrees"; fi) && \
if ! git check-ignore -q "$LOCATION" 2>/dev/null && ! rg -n "^/?${LOCATION}/?$" .gitignore >/dev/null 2>&1; then \
  printf "\n%s/\n" "$LOCATION" >> .gitignore && git add .gitignore && git commit -m "chore: ignore $LOCATION directory"; \
fi && \
WORKTREE_PATH="$(pwd -P)/$LOCATION/$BRANCH_NAME" && \
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
```

**Stateless Shell & Hook Isolation Rule (AGY / Non-Persistent Shells):**
Once `git worktree add "$WORKTREE_PATH"` succeeds, the session's `worktree-isolation-guard` hook automatically locks this conversation to `"$WORKTREE_PATH"` and blocks any `read_file`, `edit_file`, `write_file`, or `run_command` targeting the main repository checkout:
- Because each `run_command` starts in a fresh shell at the original workspace root, prefix **every** subsequent `run_command` with `cd "$WORKTREE_PATH" && ...` (including Step 2 and Step 3 below).
- Pass full paths inside `"$WORKTREE_PATH/..."` for every `read_file`, `edit_file`, and `write_file` call until `finishing-a-development-branch` is invoked.

**Sandbox fallback:** If `git worktree add` fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.

## Step 2: Project Setup

Auto-detect and run appropriate setup inside `"$WORKTREE_PATH"`:

```bash
cd "$WORKTREE_PATH" && {
  # Copy untracked local environment files if present in main repo
  MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
  for env_file in .env .env.local .env.development .env.test; do
    if [ -f "$MAIN_ROOT/$env_file" ] && [ ! -e "$env_file" ]; then
      cp "$MAIN_ROOT/$env_file" "$env_file"
    fi
  done

  # Node.js
  if [ -f package.json ]; then npm install; fi

  # Rust
  if [ -f Cargo.toml ]; then cargo build; fi

  # Python
  if [ -f uv.lock ]; then uv sync;
  elif [ -f poetry.lock ]; then poetry install;
  elif [ -f requirements.txt ]; then pip install -r requirements.txt; fi

  # Go
  if [ -f go.mod ]; then go mod download; fi
}
```

## Step 3: Verify Clean Baseline

Run tests inside `"$WORKTREE_PATH"` to ensure workspace starts clean:

```bash
# Use project-appropriate command inside the worktree
cd "$WORKTREE_PATH" && <npm test / cargo test / pytest / python3 -m unittest / go test ./...>
```

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### Report

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| Already in linked worktree | Skip creation (Step 0) |
| In a submodule | Treat as normal repo (Step 0 guard) |
| Native worktree tool available | Use it (Step 1a) |
| No native tool | Git worktree fallback (Step 1b) |
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check instruction file, then default `.worktrees/` |
| Directory not ignored | Add to .gitignore + commit |
| Permission error on create | Sandbox fallback, work in place |
| Tests fail during baseline | Report failures + ask |
| No package.json/Cargo.toml | Skip dependency install |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'm obviously not in a worktree — no need to check" | Run Step 0. Harness-created isolation and submodules both fool eyeballing; the detection commands settle it. |
| "`git worktree add` is quicker than hunting for a native tool" | A native tool (e.g. `EnterWorktree`) owns placement, branching, and cleanup. Bypassing it is the #1 mistake — it creates phantom state your harness can't see or manage. |
| "The worktree directory is surely ignored already" | Run `git check-ignore`. An unignored worktree directory commits the whole tree into the repo. |
| "Any directory name works" | Explicit instructions beat an existing project-local directory, which beats the `.worktrees/` default. |
| "The workspace is fresh — baseline tests can wait" | A dirty baseline makes every later failure ambiguous. Run the tests now; proceeding past failures is your human partner's call. |
