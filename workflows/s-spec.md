---
name: s:spec
description: Create SPEC.md for the next backlog item. Creates ./.gtd/<task_name>/SPEC.md
argument-hint: "[backlog_item]"
---

<role>
Backlog executor. Select next BACKLOG.md item and create detailed specification.
- Read BACKLOG.md to find next build target.
- Extract requirements from backlog item.
- Interview user for implementation (HOW, not WHAT).
- Write SPEC.md traceable to backlog item.
- Do not deviate from backlog.
</role>

<objective>
Create specification for a backlog item detailing implementation and exit criteria.
Flow: Read Backlog → Select Item → Research → Interview → Mirror → Confirm → Write
</objective>

<context>
Task naming: directly from BACKLOG.md item name, kebab-case (e.g. `audio-gateway`).
Required: `./.gtd/BACKLOG.md`
Output: `./.gtd/<task_name>/SPEC.md`
Skills: `research`
</context>

<philosophy>
- **Backlog Authority:** BACKLOG.md defines WHAT, Spec defines HOW. Do not ask what to build, tell user what is next.
- **No Deviation:** If not in backlog, do not build.
- **Sub-Items First:** Complete sub-items in order. Expand parent first if sub-items missing.
- **Interview for HOW:** Propose HOW, only ask about unclear items.
- **Mirroring:** Summarize implementation plan before writing.
</philosophy>

<process>

## 1. Backlog Selection Phase
```bash
if [ ! -f "./.gtd/BACKLOG.md" ]; then
    echo "Error: No BACKLOG.md found. Run /bootstrap first."
    exit 1
fi
```
Get item from argument or auto-detect first incomplete `[ ]` sub-item under active `[~]` parents in `BACKLOG.md`.

If expansion needed:
```text
---
 GTD ► NO EXECUTABLE SUB-ITEMS
---
No sub-items found. Next parent needs expansion:
**{next-parent-item}** — {description}
---
▶ Run: /expand-backlog {next-parent-item}
---
```

If sub-item found:
```text
---
 GTD ► NEXT BACKLOG ITEM
---
Based on BACKLOG.md, next item is:
**{parent}/{sub-item}** — {description}
Parent: {parent-name}
Tech: {tech stack}
---
Proceeding with research...
```

## 3. Domain Research Phase
Read `.gtd/CODEBASE.md`, `.gtd/ARCHITECTURE.md`, and `.gtd/STACK_DECISION.md`. Understand codebase state, dependencies, integration, constraints.

## 4. Interview Phase (Propose + Ask Unclear)
Propose implementation plan, ask unclear items:
```text
---
 GTD ► PROPOSED SPECIFICATION
---
For: **{parent}/{sub-item}**
**Ultimate Goal:** {outcome / why}
**Target Feature:** {backlog item}
**Must Have:**
- {requirement}
**Approach:**
- {implementation approach}
**Tech:**
- {tech stack}
**Unclear items:**
- {unclear items}
---
Please review. (ok / adjust: ...)
```
Wait for confirmation.

## 4. Write SPEC.md
Summarize implementation plan:
```text
---
 GTD ► CONFIRMING SPECIFICATION
---
**Backlog Item:** {item_name}
**Task Name:** {task-name}
**Ultimate Goal:** {outcome / why}
**Target Feature:** {backlog item}
**Must Have:** (from Backlog)
- {responsibility}
**Implementation Approach:**
- {approach}
**Tech Stack:** {tech}
**Won't Have:** {exclusions}
**Constraints:** {constraints}
---
Is this correct? (yes/no/clarify)
```
Wait for explicit confirmation.

## 5. Write SPEC.md
```bash
mkdir -p ./.gtd/<task_name>
```

Write to `./.gtd/<task_name>/SPEC.md`:
```markdown
# Specification

**Status:** FINALIZED
**Created:** {date}
**Backlog Item:** {item_name}

## Ultimate Goal

{High-level outcome / why}

## Target Feature

{What we're building — from Backlog}

## Requirements

### Must Have

- [ ] {Responsibility 1}

### Nice to Have

- [ ] {Optional feature}

### Won't Have (This Version)

- {Exclusions}

## Tech Stack

- {Technology}

## Constraints

- {Constraints}

## Implementation Notes

{Approach decisions}

## Open Questions

- {Unresolved questions}
```

</process>

<offer_next>

```text
---
 GTD ► SPEC COMPLETE ✓
---

Specification written to ./.gtd/<task_name>/SPEC.md

Backlog Item: {item_name}
Acceptance Criteria: {N} items defined

---

▶ Next Up

/roadmap — create phases from this spec

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
