---
name: plan-phase
description: Create execution plan for a phase. Creates ./.gtd/<task_name>/{phase}/PLAN.md. User manually trigger, do not auto invoke this.
argument-hint: "[phase] [--research] [--test]"
---

<role>
Plan creator. Break one roadmap phase into executable tasks with clear done criteria.
- Parse phase argument and validate against roadmap.
- Research only when needed.
- Create `PLAN.md` with atomic tasks.
- Verify plan before writing.
</role>

<objective>
Create executable `PLAN.md` for roadmap phase.
Default flow: Research (if needed) → Plan → Verify → Write
</objective>

<context>
Phase number: `$ARGUMENTS` (optional; auto-detect next unplanned phase if missing).
Flags: `--research` (force new research), `--test` (TDD failing test task).
Required: `./.gtd/<task_name>/SPEC.md`, `./.gtd/<task_name>/ROADMAP.md`
Output: `./.gtd/<task_name>/{phase}/PLAN.md`, `./.gtd/<task_name>/{phase}/RESEARCH.md` (when researched).
</context>

<decision_logic>
<discovery_levels>
| Level | When | Action |
| --- | --- | --- |
| 0 - Skip | Pure internal work, no new dependencies | No research |
| 1 - Quick | Single known library, low risk | Quick search, no `RESEARCH.md` |
| 2 - Deep | 2-3 options, new integration, high risk | Deep research and create `RESEARCH.md` |
</discovery_levels>

<complexity_rubric>
| Level | Guide (ISO 15288 Risk) | Action |
| :--- | :--- | :--- |
| **Low** | Boilerplate, CRUD, config. No concurrency/timing concerns. | Standard flow |
| **Medium** | Multiple components, edge cases, contract changes. | Standard flow, detailed tasks |
| **High** | Concurrency, state machines, ordering, data integrity. | **MANDATORY CHECKPOINT** |
Rule: Insert `checkpoint:human-verify` after High complexity task.
</complexity_rubric>

<task_types>
| Type | Use For | Autonomy |
| --- | --- | --- |
| `auto` | Work agent can complete independently | Fully autonomous |
| `checkpoint:human-verify` | Visual/functional verification | Pauses for user |
| `checkpoint:decision` | Implementation choice | Pauses for user |
</task_types>
</decision_logic>

<core_principles>
1. **Architecture Definition:** Define seams for external dependencies. No big-bang rewrites.
2. **Design Definition:** Every producer needs a consumer. No orphaned events.
3. **Traceability:** Every task maps to `SPEC.md`.
4. **Single Source of Truth:** Normal data. No duplicated state.
5. **Centralized Resilience:** Retry and circuit breakers at edge.
6. **Invariant Preservation:** State what must remain true during flight.
</core_principles>

<critical_rules>
- **Aggressive Atomicity:** **2-3 tasks max** per plan.
- **No Implementation:** Define interfaces only. No function bodies.
- **Tag Separation:** Use `<requirement>` for EARS and `<action>` for execution steps.
- **TDD Contract:** If `--test` is active, Task 1 must be TDD strategy slot.
</critical_rules>

<process>

## 1. Validate Environment
Confirm `./.gtd/<task_name>/ROADMAP.md` exists.

## 2. Parse Arguments
Get phase number, `--research`, `--test` from `$ARGUMENTS`. Auto-detect next unplanned phase if missing.

## 3. Validate Phase
Find `Phase $PHASE` in `ROADMAP.md`. Extract name and objective.

## 4. Ensure Phase Directory
Ensure `./.gtd/<task_name>/$PHASE/` exists.

## 5. Handle Research
1. Classify research need via `<discovery_levels>`.
2. For Level 2 or `--research`: investigate codebase, modules, files, dependencies, patterns, testing seams, invariants. Write findings to `./.gtd/<task_name>/$PHASE/RESEARCH.md`.

## 6. Create Plan

```text
---
  GTD ► PLANNING PHASE {N}
---
```

### 6a. Gather Context
Extract objective, requirements, constraints, invariants, non-goals, and file scope.

### 6b. Define V&V
Define: Success proof, check type, failure indicators.

### 6c. Decompose into Tasks
1. Mentally simulate implementation. Assign complexity. Identify dominant risk.
2. Break into 2-3 atomic tasks total.
3. Add safety brakes: `checkpoint:human-verify` after High tasks.
4. Map to spec requirements.
5. State invariants to preserve.

### 6d. Write PLAN.md
Write `./.gtd/<task_name>/$PHASE/PLAN.md`:

```markdown
phase: { N }
created: { date }
is_tdd: { true/false }

---

# Plan: Phase {N} - {Name}

## Objective

{What this phase delivers and why}

## V&V Strategy (Verification & Validation)

{How will we verify this phase meets requirements}

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
- **Non-Goals:** {What this phase must not expand into}

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

    ### unit: Logic Firewall ({Component Name})
    - [ ] Test: {Feature} - Happy Path
    - [ ] Test: {Feature} - Boundary Attack
    - [ ] Test: Invariant Protection

    ### integration: Boundary Guard ({Boundary Name})
    - [ ] Test: {Scenario}

    ### resilience: degradation
    - [ ] Test: gracefully degrade if dependency fails
  </action>
  <done>- Test files created and test runner reports specific failures.</done>
</task>

<!-- For standard implementation tasks: -->
<task id="2" type="auto" complexity="Medium">
  <name>{Task name}</name>
  <risk>{Rationale if complexity > Low}</risk>
  <files>{exact file paths}</files>
  <requirement>
    **When** {Trigger}, the {System} shall {Action}.
  </requirement>
  <action>
    {Exact sequence of steps - NO implementations, interfaces only}
  </action>
  <done>{Measurable criteria}</done>
</task>

<task id="2" type="auto" complexity="...">
  ...
</task>

## Success Criteria

- [ ] {Measurable outcome 1}
```

## 7. Verify Plan
Ensure 2-3 tasks max, specific, measurable done criteria, files specified, invariants explicit.

</process>

<offer_next>

```text
---
  GTD ► PHASE {N} PLANNED ✓
---

Plan written to ./.gtd/<task_name>/{phase}/PLAN.md

{X} tasks defined

---

▶ Next Up

/execute {N} — run this plan

---
```

</offer_next>

<forced_stop>
STOP. Wait for the user.
</forced_stop>
