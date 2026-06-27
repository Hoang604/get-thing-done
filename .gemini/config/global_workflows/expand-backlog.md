---
name: expand-backlog
description: Break a high-level backlog item into executable sub-items
argument-hint: "[item-name]"
---

<role>
Work breakdown specialist. Break high-level backlog item into smaller, executable pieces.
- Read specified backlog item.
- Research architecture docs to understand scope.
- Interview user about breakdown preferences.
- Break into sequential sub-items.
- Update BACKLOG.md with expanded structure.
</role>

<objective>
Expand one backlog item into sequential sub-items for /s:spec.
Flow: Read Item → Research → Interview → Propose → Confirm → Update BACKLOG.md
</objective>

<context>
Item name: $ARGUMENTS (required)
Reads: `./.gtd/BACKLOG.md`, `./.gtd/ARCHITECTURE.md`, `./.gtd/STACK_DECISION.md`
Updates: `./.gtd/BACKLOG.md` (adds sub-items under parent)
</context>

<philosophy>
- **Small Enough:** Completable in one s:spec → roadmap → execute cycle.
- **Sequential Order:** Numbered, order matters.
- **Clear Dependencies:** Note external dependencies.
- **Propose:** Decide and present. Only ask if genuinely unclear.
</philosophy>

<constraints>
## Sub-Item Format
```markdown
1.  [ ] **{parent}/{sub-name}** — {description}
```
- Prefix with parent name.
- Description in one line.
- Numbered in order.
</constraints>

<process>

## 1. Validate Arguments
```bash
if [ -z "$1" ]; then
    echo "Error: Item name required. Usage: /expand-backlog {item-name}"
    exit 1
fi
```

## 2. Find Item in Backlog
Find item in `BACKLOG.md`. Error if not found. Ask if already expanded.

## 3. Research the Item
Understand responsibilities, technologies, dependencies, and logical phases from ARCHITECTURE.md and STACK_DECISION.md.

## 4. Propose Breakdown
```text
---
 GTD ► PROPOSED BREAKDOWN: {item-name}
---

I'll break **{item-name}** into:

1. **{item}/{sub-1}** — {description}
2. **{item}/{sub-2}** — {description}

Assumptions:
- {assumption 1}

**Unclear items:**
- {unclear item}

---
Please review. (ok / adjust: ...)
```
**Wait for confirmation.**

## 5. Update BACKLOG.md
Add sub-items and change parent status to in-progress `[~]`.

**Before:**
```markdown
2. [ ] **audio-gateway** — Opus decoding, VAD, S3 upload

- **Source:** MICROSERVICE_RECOMMENDATION.md#audio-gateway
- **Tech:** Rust, Tokio, Axum
- **Responsibilities:**
  - Decode Opus to PCM
```

**After:**
```markdown
2. [~] **audio-gateway** — Opus decoding, VAD, S3 upload

- **Source:** MICROSERVICE_RECOMMENDATION.md#audio-gateway
- **Tech:** Rust, Tokio, Axum
- **Responsibilities:**
  - Decode Opus to PCM
- **Sub-items:**
  1. [ ] **audio-gateway/project-setup** — Initialize Rust project with Tokio, Axum
  2. [ ] **audio-gateway/opus-decoder** — Implement Opus to PCM decoding
```
Parent gets `[~]`, sub-items numbered and prefixed with parent name under `**Sub-items:**`.

## 7. Display Summary
```text
---
 GTD ► ITEM EXPANDED ✓
---

Parent: {item-name}
Sub-items: {N}

---
▶ Next Up
/s:spec — start the first sub-item
---
```

</process>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
