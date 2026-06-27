---
name: s:archive
description: Archive completed task/spec work to ./.gtd/archive/
argument-hint: "[task_name]"
---

<role>
Archiver. Move completed task work to archive folder.
- Verify task work exists.
- Update BACKLOG.md to mark item complete.
- Append completion event to JOURNAL.md.
- Create archive with task name and timestamp.
- Move all task files to archive.
- Clean up task folder.
</role>

<objective>
Archive completed task to keep workspace clean while preserving history.
Flow: Verify Exists → Update Backlog → Log Journal → Create Archive → Move Files → Clean Up
</objective>

<context>
Task name: $ARGUMENTS (or ask if missing).
Source: `./.gtd/<task_name>/`
Destination: `./.gtd/archive/<task_name>-{timestamp}/`
Updates: `./.gtd/BACKLOG.md` (mark item complete), `./.gtd/JOURNAL.md` (append row).
Files to archive: SPEC.md, ROADMAP.md, phase folders with PLAN.md and SUMMARY.md, task files.
</context>

<philosophy>
- **Archive When Done:** Only when task is complete or abandoned.
- **Preserve History:** Keep all files for future reference.
- **Update State:** Backlog and Journal reflect completion.
- **Clean Workspace:** Remove task folder from ./.gtd/.
</philosophy>

<process>

## 1. Determine Task Name
If no argument, ask user which task to archive from available tasks.

## 2. Check Task Exists
```bash
if [ ! -d "./.gtd/<task_name>" ]; then
    echo "Error: Task '<task_name>' not found"
    exit 1
fi
```

## 3. Update BACKLOG.md
Find `- [ ] **{task_name}**` and change `[ ]` to `[x]`.

## 4. Append to JOURNAL.md
Append table row:
```markdown
| {date} | Task completed: {task_name} | Complete | {task_name} |
```

## 5. Create Archive Directory
```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVE_DIR="./.gtd/archive/<task_name>-${TIMESTAMP}"
mkdir -p "./.gtd/archive"
```

## 6. Move Task Folder
```bash
mv "./.gtd/<task_name>" "${ARCHIVE_DIR}"
```

## 7. Commit Archive
```bash
git add ./.gtd/archive/ ./.gtd/BACKLOG.md ./.gtd/JOURNAL.md
git commit -m "chore: archive task <task_name> to {task_name}-${TIMESTAMP}"
```

## 8. Display Summary
```text
---
 GTD ► TASK ARCHIVED ✓
---

Task: {task_name}
Archived to: ./.gtd/archive/{task_name}-{timestamp}/

Phases archived: {count}
Files archived: {count}

✓ BACKLOG.md updated
✓ JOURNAL.md updated
✓ Task folder removed from ./.gtd/

---
```

</process>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
