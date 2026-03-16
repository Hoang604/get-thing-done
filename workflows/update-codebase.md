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
- You resolved an open question
- You discovered new entry points or dependencies
- You discovered a new domain or infrastructure slice worth documenting
</role>

<objective>
Incrementally update the split codebase knowledge base with verified knowledge from the current session.

**Flow:** Recall → Verify → Target → Update
</objective>

<context>
**Current Codebase Map:**

- `./.gtd/CODEBASE.md`
- `./.gtd/codebase/architecture.md`
- `./.gtd/codebase/entrypoints.md`
- `./.gtd/codebase/patterns.md`
- `./.gtd/codebase/open-questions.md`
- `./.gtd/codebase/domains/*.md`
- `./.gtd/codebase/infra/*.md`
</context>

<prohibitions>

## Same Rules as codebase-overview

**No Guessing.** Only add what you verified during this session.  
**Cite Evidence Inline.** Every changed claim must include `Evidence: path:line`.  
**Admit Gaps.** If you partially understand something, add or preserve an item in `open-questions.md`.

## Don't Rewrite Everything

This is an incremental update. Modify the smallest correct set of files.

## Don't Keep Monolith Habits

Do not dump new knowledge into `CODEBASE.md` unless the index itself needs updating.

</prohibitions>

<process>

## 1. Identify What You Learned

List the knowledge gained in this session.

Format findings like:

```text
LEARNED:
- [What changed or was clarified] — [Evidence: file:line]
```

Examples:

- `OrderProcessor.handlePayment()` calls `PaymentGateway.charge()` before `LedgerService.record()` — Evidence: `src/order/processor.ts:44`, `src/ledger/service.ts:18`
- `utils/cache.ts` is a Redis write-through adapter, not in-memory cache — Evidence: `src/utils/cache.ts:12`
- All HTTP handlers use `withTransaction()` wrapper — Evidence: `src/http/create-order.ts:9`, `src/http/refund-order.ts:11`

---

## 2. Map Findings To Target Files

Use the smallest correct target set.

| Knowledge Type | Target File |
| -------------- | ----------- |
| Repo-wide structure clarified | `architecture.md` |
| Entry point or startup flow found | `entrypoints.md` |
| Cross-cutting convention verified | `patterns.md` |
| Question answered or newly discovered gap | `open-questions.md` |
| Domain behavior clarified | `domains/<name>.md` |
| Infrastructure behavior clarified | `infra/<name>.md` |
| New domain or infra slice discovered | create new file and add link in `CODEBASE.md` |

Only update `CODEBASE.md` when:

- a new split doc is created
- a doc title or location changed
- the one-paragraph repo purpose is materially more accurate

---

## 3. Update Target Files

For each learned fact:

1. Verify the current target file exists and is still the right home
2. Update or correct the relevant section
3. Add inline evidence to each changed claim
4. Refresh `Last Updated`
5. Refresh `Last Verified` for every file you rechecked during this update

If the fact does not fit any existing file:

- create a new focused doc in `domains/` or `infra/`
- update `CODEBASE.md` to link to it

If a prior claim is stale:

- replace or remove it
- do not leave contradictory text behind

---

## 4. File-Specific Rules

### `CODEBASE.md`

- Keep it short
- Treat it as an index only
- Do not add detailed module notes here

### `architecture.md`

- Keep subsystem summaries concise
- Every subsystem entry must end with evidence

### `entrypoints.md`

- Add or correct startup flow steps only when they were traced in code
- Each flow must include evidence lines

### `patterns.md`

- Only document patterns shown in at least 2 files
- Every pattern must cite at least 2 evidence locations

### `open-questions.md`

- Remove questions that are now answered
- Add new unresolved questions when needed
- Keep the "next place to inspect" concrete when possible

### `domains/*.md` and `infra/*.md`

- Keep each file narrowly scoped
- Prefer adding facts to an existing focused doc over broadening unrelated docs
- Use flow sections for behavior and table sections for responsibilities

</process>

<output_format>

After updating, confirm:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► CODEBASE DOCS UPDATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

| File | Change |
|------|--------|
| {path} | {what changed} |

─────────────────────────────────────────────────────
```

</output_format>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
