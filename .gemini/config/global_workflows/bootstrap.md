---
name: bootstrap
description: Init backlog from architecture. Creates ./.gtd/BACKLOG.md
argument-hint: "[architecture_dir]"
---

<role>
Project initializer. Reads architecture, creates detailed backlog.
- Read docs from directory.
- Interview user for state.
- Create deep BACKLOG.md.
- Extract services, migration, infra, interfaces.
- Init JOURNAL.md.
</role>

<objective>
Create comprehensive backlog from architecture docs.
Flow: Read Docs → Interview → Extract → Write BACKLOG.md → Init JOURNAL.md
</objective>

<context>
Arch dir: $ARGUMENTS (default: `./architecture/`)
Input: `./architecture/*.md` (copied to .gtd/ first run)
Standardized (.gtd/):
- `./.gtd/ARCHITECTURE.md` (design, services, migration)
- `./.gtd/STACK_DECISION.md` (tech, constraints)
Output:
- `./.gtd/BACKLOG.md` (backlog)
- `./.gtd/JOURNAL.md` (event log)
</context>

<philosophy>
- **Deep:** Extract all details (tech, responsibilities, deps).
- **Ask:** Interview user for state, priorities, clarity.
- **Complete:** Maintain depth, clear structure.
</philosophy>

<constraints>
## Formats

### Component/Service:
```markdown
- [ ] **{kebab-case-name}** — {one-line description}
  - **Source:** {filename}#{section-heading}
  - **Tech:** {comma-separated technologies}
  - **Responsibilities:**
    - {responsibility 1}
    - {responsibility 2}
```

### Migration (Sequential):
```markdown
1. [ ] **{kebab-case-name}** — {one-line description}
   - **Source:** {filename}#{section-heading}
   - **Depends:** none | {previous-step-name}
```

### Rules:
- `name` MUST be kebab-case (e.g. `audio-gateway`).
- `Tech` comma-separated.
- `Responsibilities` sub-bullets.
- `Source` links to section.
- Migration items use numbered list.
</constraints>

<process>

## 1. Validate Environment

```bash
ARCH_DIR="${1:-./architecture}"
if [ ! -d "$ARCH_DIR" ]; then
    echo "Error: Architecture directory not found: $ARCH_DIR"
    exit 1
fi
mkdir -p ./.gtd
```

---

## 2. Setup Architecture Files

Check `.gtd/` files:

```bash
if [ ! -f "./.gtd/ARCHITECTURE.md" ]; then
    echo "No .gtd/ARCHITECTURE.md found."
fi
if [ ! -f "./.gtd/STACK_DECISION.md" ]; then
    echo "No .gtd/STACK_DECISION.md found."
fi
```

- If `./architecture/` files exist: copy to `.gtd/ARCHITECTURE.md` and `.gtd/STACK_DECISION.md`.
- Else: read directly from `.gtd/`.

---

## 3. Read Architecture Documents

Read:
- `./.gtd/ARCHITECTURE.md` (services, migration, interfaces)
- `./.gtd/STACK_DECISION.md` (tech constraints)

Extract:
- Services/Components (responsibilities, tech)
- Migration steps (ordering)
- Infra deps
- Interfaces/protocols

---

## 4. Interview Phase

Propose findings, ask unclear:

```text
---
 GTD ► BOOTSTRAP PROPOSAL
---

I've read your architecture docs. Here's what I'll create:

**Migration Steps:** (in order)
1. {step-1} — {description}
2. {step-2} — {description}

**Components:**
- {component-1} — {description}
- {component-2} — {description}

**I'm assuming these already exist (will skip), please verify:**
- Kafka, Redis, S3 (infrastructure)

**I'm assuming the following ..., please verify:**
- {assumption 1}
- {assumption 2}

**Unclear items (need your input):**
- {unclear item, if any}

---
Please review. (ok / adjust: ...)
```

**Wait for user confirmation.**

---

## 5. Write BACKLOG.md

Write to `./.gtd/BACKLOG.md`:

```markdown
# Project Backlog

**Created:** {date}
**Source:** {architecture_dir}

## Legend

- [ ] Not started
- [~] In progress (being expanded or executed)
- [x] Complete

---

## Migration

(Sequential steps — MUST be executed in order before Components)

1. [ ] **{step-name}** — {description}
   - **Source:** {filename}#{section}
   - **Depends:** none

2. [ ] **{step-name}** — {description}
   - **Source:** {filename}#{section}
   - **Depends:** {previous-step-name}

---

## Interfaces

(Shared contracts — should be done early)

- [ ] **{protocol-name}** — {purpose}
  - **Source:** {filename}#{section}
  - **Tech:** {technology}

---

## Components

(Services to build — can be parallelized after Migration complete)

- [ ] **{service-name}** — {one-line description}
  - **Source:** {filename}#{section}
  - **Tech:** {technology1}, {technology2}
  - **Responsibilities:**
    - {responsibility 1}
    - {responsibility 2}

---

## Infrastructure

(Supporting systems — skip if already exists)

- [ ] **{component-name}** — {purpose}
  - **Source:** {filename}#{section}
  - **Tech:** {technology}

---

## Completed
```

---

## 6. Initialize JOURNAL.md

Write to `./.gtd/JOURNAL.md`:

```markdown
# Project Journal

**Created:** {date}

| Date   | Event                                        | Item |
| ------ | -------------------------------------------- | ---- |
| {date} | Project bootstrapped from {architecture_dir} | —    |
```

---

## 7. Display Summary

```text
---
 GTD ► PROJECT BOOTSTRAPPED ✓
---

Backlog: ./.gtd/BACKLOG.md
Journal: ./.gtd/JOURNAL.md

| Section        | Items |
|----------------|-------|
| Migration      | {N}   |
| Interfaces     | {N}   |
| Components     | {N}   |
| Infrastructure | {N}   |

---
▶ Next Up
/expand-backlog {first-item} — break it into executable pieces
  OR
/s:spec — if items are already detailed enough
---
```

</process>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
