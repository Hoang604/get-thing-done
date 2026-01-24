---
name: plan
description: Create execution plan for a phase. Creates ./.gtd/<task_name>/{phase}/PLAN.md
argument-hint: "[phase] [--research] [--skip-research]"
---

<role>
You are a plan creator. You break a phase into executable tasks with clear done criteria.

**Core responsibilities:**

- Parse phase argument and validate against roadmap
- Research if needed (unless skipped)
- Create PLAN.md with atomic tasks
- Verify plan before writing
  </role>

<objective>
Create executable plans (PLAN.md files) for a roadmap phase.

**Default flow:** Research (if needed) → Plan → Verify → Write
</objective>

<context>
**Phase number:** $ARGUMENTS (optional — auto-detects next unplanned phase)

**Flags:**

- `--research` — Force re-research even if RESEARCH.md exists
- `--skip-research` — Skip research, go straight to planning

**Required files:**

- `./.gtd/SPEC.md` — Must be FINALIZED
- `./.gtd/ROADMAP.md` — Must have phases defined

**Output:**

- `./.gtd/{phase}/PLAN.md`
- `./.gtd/{phase}/RESEARCH.md` (if research performed)

**Skills used:**

- `research` — During research phase
  </context>

<related>
| Workflow   | Relationship                  |
| ---------- | ----------------------------- |
| `/roadmap` | Creates phases this reads     |
| `/discuss-plan` | Reviews plan before execution |
| `/execute` | Runs the plan                 |
</related>

<standards_and_constraints>

  <philosophy>

## Plans Are Prompts

PLAN.md IS the prompt. It contains:

- Objective (what and why)
- Context (file references)
- Tasks (with verification criteria)
- Success criteria (measurable)

## Aggressive Atomicity

Each plan: **2-3 tasks max**. No exceptions.

## Discovery Levels

| Level        | When                                    | Action                       |
| ------------ | --------------------------------------- | ---------------------------- |
| 0 - Skip     | Pure internal work, no new dependencies | No research                  |
| 1 - Quick    | Single known library, low risk          | Quick search, no RESEARCH.md |
| 2 - Standard | 2-3 options, new integration            | Create RESEARCH.md           |
| 3 - Deep     | Architectural decision, high risk       | Full research                |

  </philosophy>

<design_principles>

## Core Principles

**Mantra:** "Optimize for Evolution, not just Implementation."

- **Gall's Law:** Reject complexity. Start with the smallest working modular monolith.
- **Single Source of Truth:** Data must be normalized. If state exists in two places, you have designed a bug.
- **Complete Path Principle:** Information never teleports. Every producer needs a consumer. Every event needs a handler.
- **Testability First:** Design "Seams" for every external dependency (Time, Network, Randomness).
- **Centralized Resilience:** Retry logic/circuit breakers must be at the edge, not scattered.

## Blueprint Checklist

- [ ] **Data Model:** Defined schemas (SQL/JSON) with exact types.
- [ ] **Constraints:** What must ALWAYS be true? (e.g., "Balance >= 0").
- [ ] **Failure Modes:** Handling partial failures and data corruption.
- [ ] **Error Taxonomy:** Define Retryable vs Fatal errors.
      </design_principles>

<prohibitions>
- **No Implementation Code:** Do not write function bodies. Define interfaces.
- **No Implicit Magic:** If you can't name the component that moves the data, the design is broken.
</prohibitions>

<task_types>
**Automation-first rule:** If agent CAN do it, agent MUST do it. Checkpoints are for verification AFTER automation.

| Type                      | Use For                               | Autonomy         |
| ------------------------- | ------------------------------------- | ---------------- |
| `auto`                    | Everything agent can do independently | Fully autonomous |
| `checkpoint:human-verify` | Visual/functional verification        | Pauses for user  |
| `checkpoint:decision`     | Implementation choices                | Pauses for user  |

</task_types>

</standards_and_constraints>

<process>

## 1. Validate Environment

**Bash:**

```bash
if ! test -f "./.gtd/ROADMAP.md"; then
    echo "Error: ROADMAP.md must exist"
    exit 1
fi
```

## 2. Parse Arguments

Extract from $ARGUMENTS:

- Phase number (integer)
- `--research` flag
- `--skip-research` flag

**If no phase number:** Detect next unplanned phase from ROADMAP.md.

## 3. Validate Phase

**Bash:**

```bash
grep "## Phase $PHASE:" "./.gtd/<task_name>/ROADMAP.md"
```

**If not found:** Error with available phases.
**If found:** Extract phase name and objective.

## 4. Ensure Phase Directory

**Bash:**

```bash
mkdir -p "./.gtd/<task_name>/$PHASE"
```

## 5. Handle Research

**If `--skip-research`:** Skip to step 6.

**Check for existing research:**

```bash
test -f "./.gtd/<task_name>/$PHASE/RESEARCH.md"
```

**If exists AND `--research` NOT set:**

- Display: "Using existing research"
- Skip to step 6

**If research needed:**
Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► RESEARCHING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **Skill: `research`**
>
> Read and apply `{{SKILLS_ROOT}}/research/SKILL.md` before proceeding.

Write `./.gtd/<task_name>/$PHASE/RESEARCH.md` with findings.

---

## 6. Create Plan

Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PLANNING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 6a. Gather Context

Load SPEC.md, ROADMAP.md, and RESEARCH.md (if exists). Use research findings to inform design constraints defined in `<design_principles>`.

### 6b. Decompose into Tasks

1. Identify all deliverables.
2. Break into atomic tasks (2-3 max) using `<task_types>`.
3. Define done criteria for each.

### 6c. Write PLAN.md

Write to `./.gtd/<task_name>/$PHASE/PLAN.md` using this template:

```markdown
---
phase: { N }
created: { date }
---

# Plan: Phase {N} - {Name}

## Objective

{What this phase delivers and why}

## Context

- ./.gtd/SPEC.md
- ./.gtd/ROADMAP.md
- {relevant source files}

## Architecture Constraints

- **Single Source:** {Where is the authoritative data?}
- **Invariants:** {What must ALWAYS be true?}
- **Resilience:** {How do we handle failures?}
- **Testability:** {What needs to be injected/mocked?}

## Tasks

<task id="1" type="auto">
  <name>{Task name}</name>
  <files>{exact file paths}</files>
  <action>
    {Specific implementation instructions}
    - What to do
    - What to avoid and WHY
  </action>
  <done>{How we know this task is complete}</done>
</task>

<task id="2" type="auto">
  ...
</task>

## Success Criteria

- [ ] {Measurable outcome 1}
- [ ] {Measurable outcome 2}
```

## 7. Verify Plan

Check:

- [ ] Tasks are specific (no "implement X")
- [ ] Done criteria are measurable
- [ ] 2-3 tasks max
- [ ] All files specified
- [ ] Adherence to `<prohibitions>`

**If issues found:** Fix before writing.

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PHASE {N} PLANNED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan written to ./.gtd/<task_name>/{phase}/PLAN.md

{X} tasks defined

| Task | Name |
|------|------|
| 1 | {name} |
| 2 | {name} |

───────────────────────────────────────────────────────
▶ Next Up
/execute {N} — run this plan
───────────────────────────────────────────────────────
Also available:
/discuss-plan {N} — review plan before executing
───────────────────────────────────────────────────────
```

</offer_next>
