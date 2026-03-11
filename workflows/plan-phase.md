---
name: plan-phase
description: Create execution plan for a phase. Creates ./.gtd/<task_name>/{phase}/PLAN.md
argument-hint: "[phase] [--research] [--test]"
---

<role>
You are a plan creator. Break one roadmap phase into executable tasks with clear done criteria.

**Core responsibilities:**

- Parse the phase argument and validate it against the roadmap
- Research only when needed
- Create `PLAN.md` with atomic tasks
- Verify the plan before writing
</role>

<objective>
Create an executable `PLAN.md` for a roadmap phase.

**Default flow:** Research (if needed) → Plan → Verify → Write
</objective>

## User Request Current Phase
{{args}}

<context>
**Phase number:** `$ARGUMENTS` (optional; auto-detect the next unplanned phase if missing)

**Flags:**

- `--research` — Force new research even if `RESEARCH.md` already exists
- `--test` — Make Task 1 a TDD "Create Failing Test" task

**Required files:**

- `./.gtd/<task_name>/SPEC.md` — Must be `FINALIZED/UPDATED`
- `./.gtd/<task_name>/ROADMAP.md` — Must define phases

**Output:**

- `./.gtd/<task_name>/{phase}/PLAN.md`
- `./.gtd/<task_name>/{phase}/RESEARCH.md` when research is performed

</context>

<decision_logic>

<discovery_levels>
| Level | When | Action |
| ------------ | --------------------------------------- | ---------------------------- |
| 0 - Skip | Pure internal work, no new dependencies | No research |
| 1 - Quick | Single known library, low risk, related to some files | Quick search, no `RESEARCH.md` |
| 2 - Deep | 2-3 options, new integration, multiple components, Architectural decision, high risk | Research via `spawn_agent` and tell the agent to create `RESEARCH.md` |

</discovery_levels>

<complexity_rubric>
| Level | Guide (ISO 15288:6.3.4 Risk Management) | Action |
| :--------- | :--------------------------------------------------------------------------------------
| :--------------------------------- |
| **Low** | Boilerplate, CRUD, wiring, config. No shared state or timing concerns. | Standard flow |
| **Medium** | Multiple components, edge cases, or contract changes. | Standard flow, detailed tasks |
| **High** | Concurrency, state machines, ordering, data integrity, or dynamic env. | **MANDATORY CHECKPOINT** |

**Rule for High Complexity:**
1. Insert `checkpoint:human-verify` immediately after the risky task.
2. State the risk in terms of system integrity.
</complexity_rubric>

<task_types>
| Type | Use For | Autonomy |
| ------------------------- | ------------------------------------- | ---------------- |
| `auto` | Work the agent can complete independently | Fully autonomous |
| `checkpoint:human-verify` | Visual/functional verification | Pauses for user |
| `checkpoint:decision` | Implementation choice | Pauses for user |
</task_types>

</decision_logic>

<core_principles>
1. **Architecture Definition (15288:6.4.4):** Define seams for external dependencies. No big-bang rewrites.
2. **Design Definition (15288:6.4.5):** Every producer needs a consumer. No orphaned events.
3. **Traceability:** Every task MUST map back to a requirement in `SPEC.md`.
4. **Single Source of Truth:** Data MUST be normalized. No duplicated state.
5. **Centralized Resilience:** Retry logic and circuit breakers MUST stay at the edge.
</core_principles>

<critical_rules>
- **Aggressive Atomicity:** Each plan MUST have **2-3 tasks max**.
- **No Implementation:** Do not write function bodies. Define interfaces only.
- **Tag Separation:** Use `<requirement>` for EARS behavior and `<action>` for exact execution steps.
- **TDD Contract:** If `--test` is active, Task 1 MUST be `<!-- TDD_STRATEGY_SLOT -->`.
</critical_rules>

<process>

## 1. Validate Environment

Confirm `./.gtd/<task_name>/ROADMAP.md` exists.

## 2. Parse Arguments

Extract from `$ARGUMENTS` when available:

- Phase number
- `--research`
- `--test`

If no phase number is provided, detect the next unplanned phase from `ROADMAP.md`.

## 3. Validate Phase

Find `Phase $PHASE` in `./.gtd/<task_name>/ROADMAP.md`.

- If not found, stop and report the available phases.
- If found, extract the phase name and objective.

## 4. Ensure Phase Directory

Ensure `./.gtd/<task_name>/$PHASE/` exists.

## 5. Handle Research

### 5a. Assign discovery level

Use the phase objective and `<discovery_levels>` to classify research needs.

### 5b. Choose the research path

- **Level 0:** skip research.
- **Level 1:** inspect the code locally for specific unknowns. Do not create `RESEARCH.md`.
- **Level 2** or `--research`:
  - Check whether `./.gtd/<task_name>/$PHASE/RESEARCH.md` already exists.
  - If it exists and `--research` is not set, reuse it.
  - Otherwise, research with a subagent.
  
**If research needed:**
Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► RESEARCHING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

> **Skill: `research`**
>
> use tool to read `{{SKILLS_ROOT}}/research/SKILL.md` before proceeding. Do not lazy.
then use the skills to answer these question:
1. Which files/modules are most relevant to this phase?
2. What existing patterns or abstractions should be reused?
3. What constraints, edge cases, or risks could affect planning?
4. What testing seams or dependency boundaries are available?
5. What file-level scope should PLAN.md reference explicitly?


Write `./.gtd/<task_name>/$PHASE/RESEARCH.md` with findings.

---

## 6. Create Plan

Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PLANNING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
### 6b. Decompose into Tasks

1. **Calibrate each task**
    - Mentally simulate the implementation before finalizing the task.
    - Assign a complexity level: Low, Medium, or High.
    - If the implementation path is unclear or risky, mark it as **High**.

2. **Break the phase into atomic tasks**
    - Create 2-3 tasks total.
    - Each task should represent one clear deliverable or verification step.

3. **Add safety brakes where needed**
    - If a task is **High** complexity, insert a `checkpoint:human-verify` task immediately after it.
    - Use checkpoint text in this form: `"STOP. Review the implementation of {file} for {specific_risk}."`

4. **Map the phase to spec requirements**
    - Identify the Must Have and Nice To Have requirements from `SPEC.md` covered by this phase.
    - List them explicitly for traceability.

### 6c. Write PLAN.md

Write to `./.gtd/<task_name>/$PHASE/PLAN.md` using this template:

```markdown
phase: { N }
created: { date }
is_tdd: { true/false }

---

# Plan: Phase {N} - {Name}

## Objective

{What this phase delivers and why}

## V&V Strategy (Verification & Validation)

{How will we verify this phase meets requirements - 15288:6.4.9/10}

## Spec Requirements (Traceability)

- [ ] Must Have: {Requirement 1}
- [ ] Nice To Have: {Requirement 2}

## Context

- ./.gtd/<task_name>/SPEC.md
- ./.gtd/<task_name>/ROADMAP.md
- {relevant source files}

## Architecture Constraints

- **Single Source:** {Where is the authoritative data}
- **Invariants:** {What must ALWAYS be true}
- **Decision Rationale:** {Why this architectural choice was made}
- **Testability:** {What needs to be injected/mocked (Design Seams)}

## Tasks

<!-- If --test flag IS SET, task 1 is write test: -->
<task id="1" type="auto" complexity="High">
  <name>TDD Strategy Formulation: {Phase Name}</name>
  <risk>Prevents architectural drift and regression through invariant protection.</risk>
  <files>{Specific test files to be created}</files>
  <requirement>
    - **When** the tests are run, **then** they shall fail until the implementation is complete.
  </requirement>
  <action>
    Implement test suites in {files}. Ensure tests FAIL (Red) before starting implementation.

    ### 1. Unit: The Logic Firewall ({Component Name})
    - [ ] Test: {Feature} - Happy Path -> Returns {Result}
    - [ ] Test: {Feature} - Boundary Attack -> Handles gracefully
    - [ ] Test: Invariant Protection -> Rejects invalid transition

    ### 2. Integration: The Boundary Guard ({Boundary Name})
    - [ ] Test: {Scenario} - Flow maintains system integrity.

    ### 3. Resilience & Errors
    - [ ] Test: Failure Recovery - **If** dependency fails, **then** system degrades gracefully.
  </action>
  <done>- Test files created and test runner reports specific failures.</done>
</task>

<!-- For standard implementation tasks: -->
<task id="2" type="auto" complexity="Medium">
  <name>{Task name}</name>
  <risk>{Rationale if complexity > Low}</risk>
  <self_audit>
    - Security: {Risk: ...}
    - Performance: {Risk: ...}
    - 15288 Architecture/Design Gap: {Risk: ...}
  </self_audit>
  <files>{exact file paths}</files>
  <requirement>
    **When** {Trigger}, the {System} shall {Action}...
  </requirement>
  <action>
    {Exact sequence of agent tool calls / code edits}
    - Modify {file} to implement {logic}
    - Ensure {invariants} are maintained as per {self_audit}
  </action>
  <done>{EARS-based criteria: e.g. "The system shall..."}</done>
</task>

## Success Criteria (Measurable)

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

─────────────────────────────────────────────────────
▶ Next Up
/execute {N} — run this plan
─────────────────────────────────────────────────────
Also available:
/discuss-plan {N} — review plan before executing
─────────────────────────────────────────────────────
```

</offer_next>

<forced_stop>
Do NOT automatically run the next command. Wait for the user.
</forced_stop>
