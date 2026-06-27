---
name: archive
description: Archive completed task/spec work to ./.gtd/archive/
argument-hint: "[task_name]"
---

<role>
Archiver. Move completed task work to archive folder.
- Verify task work exists.
- Create archive with task name and timestamp.
- Move task files to archive.
- Clean up task folder.
</role>

<objective>
Archive completed task to keep workspace clean.
Flow: Verify Exists → Create Archive → Move Files → Clean Up
</objective>

<context>
Task name: $ARGUMENTS (if none, ask user)
Source: `./.gtd/<task_name>/`
Destination: `./.gtd/archive/<task_name>-{timestamp}/`
Files: SPEC.md, ROADMAP.md, phase folders, other task files.
</context>

<philosophy>
- **Archive When Done:** Only when task complete/abandoned.
- **Preserve History:** Keep all files.
- **Clean Workspace:** Remove task folder.
</philosophy>

<process>

## 1. Determine Task Name

If no argument:

```text
Which task would you like to archive?

Available tasks:
- {task 1}
- {task 2}
```

---

## 2. Check Task Exists

Verify `./.gtd/<task_name>/` exists:

```bash
if [ ! -d "./.gtd/<task_name>" ]; then
    echo "Error: Task '<task_name>' not found"
    exit 1
fi
```

---

## 3. Create Archive Directory

Generate name with timestamp:

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVE_DIR="./.gtd/archive/<task_name>-${TIMESTAMP}"
mkdir -p "./.gtd/archive"
```

---

## 4. Move Task Folder

Move to archive:

```bash
mv "./.gtd/<task_name>" "${ARCHIVE_DIR}"
```

---

## 5. Commit Archive

```bash
git add ./.gtd/archive/
git commit -m "chore: archive task <task_name> to {task_name}-${TIMESTAMP}"
```

---

## 6. Display Summary

```text
---
 GTD ► TASK ARCHIVED ✓
---

Task: {task_name}
Archived to: ./.gtd/archive/{task_name}-{timestamp}/

Phases archived: {count}
Files archived: {count}

Task folder removed from ./.gtd/

---
```

</process>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
