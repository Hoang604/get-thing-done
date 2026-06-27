---
name: roadmap
description: Create sequential phases from spec. Creates ./.gtd/<task_name>/ROADMAP.md. User manually trigger, do not auto invoke this.
---

<role>
Project sequencer. Convert finalized spec into small set of dependency-ordered phases.
- Validate SPEC.md is ready.
- Extract requirements and constraints.
- Group work into usable phases.
- Make requirement coverage explicit.
- Write `ROADMAP.md`.
</role>

<objective>
Create roadmap (ROADMAP.md): ordering, deliverables, and requirement coverage.
Flow: Validate Spec → Extract → Optional Constraint Check → Group → Order → Coverage Check → Write
</objective>

<context>
Input: Task name from arguments or inferred. `./.gtd/<task_name>/SPEC.md` must exist and be FINALIZED or UPDATED.
Output: `./.gtd/<task_name>/ROADMAP.md`
</context>

<philosophy>
- **Deliverables:** Each phase must leave system usable/testable.
- **EARS Alignment:** Phase objectives and success criteria use EARS syntax where possible:
  - **When** {trigger}, the {System} shall {action}.
  - **While** {state}, the {System} shall {action}.
  - **If** {condition}, then the {System} shall {action}.
- **Dependency Order:** Later phases build on earlier ones. Minimize risky transitional states.
- **Keep Small:** 3-5 phases total.
- **Coverage Explicit:** Every Must-Have requirement assigned to at least one phase.
</philosophy>

<process>

## 1. Validate the Spec
Ensure `SPEC.md` exists, status `FINALIZED` or `UPDATED`, contains Problem, Goal, Feature, Requirements, Constraints, Invariants, and Done Criteria.

## 2. Extract the Planning Inputs
Extract problem, goal, feature, requirements (Must-Have, Nice-to-Have), constraints, invariants, non-goals, and done criteria.

## 3. Optional Constraint Check
Investigate codebase constraints, rollout order, boundary risks, and dependencies. Keep notes on sequence.

## 4. Group Requirements Into Phases
Group coupled requirements into verifiable phases. No split invisible capabilities unless dependencies force it.

## 5. Order the Phases
Unlock next phases or reduce risk. Standard shape: Foundation → Core path → Hardening → Optional. Respect invariants.

## 6. Write ROADMAP.md
Write `./.gtd/<task_name>/ROADMAP.md`:

```markdown
# Roadmap

**Spec:** ./.gtd/<task_name>/SPEC.md
**Current Problem:** {current_problem}
**Ultimate Goal:** {ultimate_goal}
**Target Feature:** {target_feature}
**Created:** {date}

## Strategy

{Explain how the ordered phases reach the goal}

## Constraints & Invariants

- Constraint: {hard system constraint}
- Must Preserve: {invariant}

## Must-Haves

- [ ] {requirement 1}

## Nice-To-Haves

- [ ] {optional requirement 1}

## Phases

### Phase 1: {name}

**Status**: ⬜ Not Started
**Objective**: **When** this phase is complete, the {System} shall {outcome}.

**Covers Requirements:**
- Must Have: {requirement}
- Nice to Have: {optional requirement if any}

**Exit Criteria:**
- {measurable completion statement}

### Phase 2: {name}
...
```

## 7. Coverage Check
Verify: all Must-Haves assigned, Nice-to-Haves marked optional, phases ordered correctly, objectives measurable, invariants respected, non-goals excluded.

## 8. Final Readiness Check
Ensure roadmap is ready for `plan-phase` with clear exit criteria.

</process>

<offer_next>

```text
---
  GTD ► ROADMAP COMPLETE ✓
---

Roadmap written to ./.gtd/<task_name>/ROADMAP.md

{N} phases defined
Coverage: 100% of Must-Have requirements assigned

---

▶ Next Up

/plan-phase 1 — create execution plan for Phase 1

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
