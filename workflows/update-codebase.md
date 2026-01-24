---
name: update-codebase
description: Update CODEBASE.md with working knowledge gained during task execution
argument-hint: "[section-hint]"
---

<role>
You are updating the codebase map with newly discovered knowledge.

**When to use this:**

- You've traced a flow and now understand it better
- You discovered undocumented patterns or conventions
- You found a module's true purpose differs from documented
- You resolved an "Open Question" from CODEBASE.md
- You discovered new entry points or dependencies
  </role>

<objective>
Incrementally update `./.gtd/CODEBASE.md` with verified knowledge from current session.

**Flow:** Recall → Verify → Update
</objective>

<prohibitions>

## Same Rules as codebase-overview

**No Guessing.** Only add what you verified during this session.  
**Cite Evidence.** Every update must reference the file/line you learned it from.  
**Admit Gaps.** If you partially understand something, add to Open Questions instead.

## Don't Rewrite Everything

This is an incremental update. You modify specific sections, not the whole document.

</prohibitions>

<process>

## 1. Load Current State

Verify `./.gtd/CODEBASE.md` exists and read it:

```bash
test -f ./.gtd/CODEBASE.md && echo "EXISTS" || echo "MISSING"
```

**If MISSING:** Stop. User should run `/codebase-overview` first.

**If EXISTS:** Read the entire CODEBASE.md now. You need current state to:

- Know what's already documented (avoid duplicates)
- See existing Open Questions you might have resolved
- Understand section structure for targeted updates

Use `view_file/read_file` tool on `./.gtd/CODEBASE.md` to read the full contents.

---

## 2. Identify What You Learned

List the knowledge gained in this session. Examples:

- "Discovered `OrderProcessor.handlePayment()` calls `PaymentGateway.charge()` → `LedgerService.record()` flow"
- "Found that `utils/cache.ts` is actually a write-through cache to Redis, not in-memory"
- "Identified pattern: all handlers use `withTransaction()` wrapper"

**Format your findings:**

```
LEARNED:
- [What] — [Evidence: file:line or flow traced]
```

---

## 3. Map to CODEBASE.md Sections

| Knowledge Type             | Section to Update       |
| -------------------------- | ----------------------- |
| Module purpose clarified   | Modules → {Module Name} |
| New pattern discovered     | Patterns & Conventions  |
| Entry point found          | Entry Points            |
| Dependency usage clarified | Dependencies (Key)      |
| Question answered          | Open Questions (remove) |
| New question emerged       | Open Questions (add)    |

---

## 4. Make Targeted Updates

For each piece of knowledge:

1. Read the relevant CODEBASE.md section
2. Update only that section
3. Add `**Updated:** {date}` annotation if significant change

**Update rules:**

- **Adding info:** Append to existing sections
- **Correcting info:** Replace with new, add note: `(Corrected: was {old}, actually {new})`
- **Removing Open Question:** Delete the question, add the answer to appropriate section

---

## 5. Record Update Log

At the bottom of CODEBASE.md, maintain an update log:

```markdown
## Update Log

| Date   | Session         | Updates            |
| ------ | --------------- | ------------------ |
| {date} | {brief context} | {sections changed} |
```

</process>

<output_format>

After updating, confirm:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► CODEBASE.md UPDATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| Section | Change |
|---------|--------|
| {section} | {what changed} |

───────────────────────────────────────────────────────
```

</output_format>
