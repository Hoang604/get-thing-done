---
name: d-archive
description: Archive completed debug work to ./.gtd/archive/
---

<role>
Archiver. Move completed debug work to archive folder.
- Check if current debug work is complete.
- Create archive with timestamp.
- Move debug files to archive.
- Clean up current debug folder.
</role>

<objective>
Archive completed debug investigation to keep workspace clean.
Flow: Verify Complete → Create Archive → Move Files → Clean Up
</objective>

<context>
Source: `./.gtd/debug/current/`
Destination: `./.gtd/archive/debug-{timestamp}/`
Files: SYMPTOM.md, HYPOTHESES.md, ROOT_CAUSE.md, FIX_PLAN.md, FIX_SUMMARY.md.
</context>

<philosophy>
- **Archive When Done:** Only when debug work is complete/abandoned.
- **Preserve History:** Keep all files.
- **Clean Current:** Empty current/ folder.
</philosophy>

<process>

## 1. Check Current Debug Work

Verify `./.gtd/debug/current/` has files:

```bash
if [ ! -d "./.gtd/debug/current" ] || [ -z "$(ls -A ./.gtd/debug/current)" ]; then
    echo "No debug work to archive"
    exit 0
fi
```

---

## 2. Create Archive Directory

Generate timestamped name:

```bash
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
ARCHIVE_DIR="./.gtd/archive/debug-${TIMESTAMP}"
mkdir -p "${ARCHIVE_DIR}"
```

---

## 3. Move Files

Move files to archive:

```bash
mv ./.gtd/debug/current/* "${ARCHIVE_DIR}/"
```

---

## 4. Commit Archive

```bash
git add ./.gtd/archive/
git commit -m "chore: archive debug work to debug-${TIMESTAMP}"
```

---

## 5. Display Summary

```text
---
 GTD ► DEBUG WORK ARCHIVED ✓
---

Archived to: ./.gtd/archive/debug-{timestamp}/

Files archived: {count}

Current debug folder is now empty and ready for next investigation.

---
```

</process>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
