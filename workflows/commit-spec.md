---
name: commit-spec
description: Create commit from spec phases and commit all changes.
argument-hint: ""
---

<role>
Commit message composer. Read phase summaries, make conventional commit, commit all.
- Read SUMMARY.md from completed phases.
- Synthesize into commit message.
- Commit all changes.
- Use conventional commits.
</role>

<objective>
Compose short conventional commit and execute.
Flow: Summaries → Compose → Commit
</objective>

<context>
Inputs:
- `./.gtd/<task_name>/ROADMAP.md` (roadmap)
- `./.gtd/<task_name>/{phase}/SUMMARY.md` (completed phase summaries)
Output:
- Git commit
</context>

<philosophy>
- **Terse:** Keep message short.
- **Why over What:** Explain reasoning, not diff.
- **Skip Body:** No body if subject is clear. Only use body for breaking changes, migration, revert, or non-obvious why.
- **Conventional:** Use exact types (`feat`, `fix`, `refactor`, etc.).
</philosophy>

<process>

## 1. Load Roadmap

Read `./.gtd/<task_name>/ROADMAP.md` to identify completed phases.

```bash
if ! grep -q "✅ Complete" "./.gtd/<task_name>/ROADMAP.md"; then
    echo "Error: No completed phases found"
    exit 1
fi
```

---

## 2. Gather Phase Summaries

Read `./.gtd/<task_name>/{phase}/SUMMARY.md` for completed phases.

Extract:
- What was done
- Behaviour changes (before/after)
- Files changed
- Key deviations

---

## 3. Synthesize Commit Message

Create conventional commit message.

**Format:**

```
{type}({scope}): {short description}

{Body: Explain WHY. Skip body if subject is clear.
Use only for breaking change, migration, revert, or non-obvious context.}

{BREAKING CHANGE: describe if any}
```

**Guidelines:**
- **Type:** conventional type.
- **Scope:** spec/feature name.
- **Short description:** Imperative mood, max 50 chars, no trailing period.
- **Body:** Focus on WHY, not what. Skip if obvious.

---

## 4. Stage All Changes

```bash
git add .
```

---

## 5. Create Commit

Write message to file, then commit:

```bash
# 1. Write message to file (use write_to_file tool)
# 2. Commit
git commit -F .gtd/COMMIT_MSG.txt
# 3. Clean up
rm .gtd/COMMIT_MSG.txt
```

---

## 6. Display Summary

```text
---
 GTD ► SPEC COMMITTED ✓
---

Phases committed: {count}
Files changed: {count}

Commit message preview:
{first 3 lines of commit message}
...

---
▶ View Full Commit

git show HEAD
---
▶ Next Up
/update-codebase update .gtd/CODEBASE.md to reflect the new change
---
```

</process>

<examples>

## Example Commit Message

```
feat(user-auth): transition to JWT to support horizontal scaling

- Replaces stateful session cookies to allow stateless backend clustering.
```

</examples>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
