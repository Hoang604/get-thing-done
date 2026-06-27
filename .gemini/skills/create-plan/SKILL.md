---
name: create-plan
description: create plan follow the incose/ears format and iso/iec/ieee 15288:2023 conformance
---

<role>
Write plans following ISO 15288:2023 (Systems Engineering) and EARS syntax.
- Ground plan in codebase reality.
- Challenge approach vs goal.
- Mirror summary and wait for user confirmation before writing plan.
- Produce unambiguous, verifiable requirements.
</role>

<objective>
Draft `implementation_plan.md` artifact.
Flow: Gather Context → Resolve References → Frame Reality → Assess Risk → Challenge Fit → Mirror → Confirm → Write Plan
</objective>

<philosophy>
## ISO 15288:2023 Technical Processes
- **Architecture Definition (6.4.4):** Define boundaries, interfaces, seams.
- **Design Definition (6.4.5):** Specify files/lines to modify.
- **Verification (6.4.9):** Prove built right (Lints, build, static checks).
- **Validation (6.4.10):** Prove right system built (Tests, scenarios, feedback).

## EARS Requirement Syntax
Requirements MUST use:
- **Ubiquitous:** System shall `<Action>`.
- **Event:** **When** `<Trigger>`, system shall `<Action>`.
- **State:** **While** `<State>`, system shall `<Action>`.
- **Unwanted:** **If** `<Condition>`, **then** system shall `<Action>`.
- **Optional:** **Where** `<Feature>`, system shall `<Action>`.

## Solve Right Problem
Challenge approach if it does not serve user goal. Stop and discuss if weak.

## Ask Codebase First
Inspect code before asking user. Only ask user for:
- Why they want change
- Expected outcome
- What must not break
- Choice between valid interpretations

## Define Reality
Capture current state: pain/failure, evidence, constraints, invariants, out of scope.
</philosophy>

<process>

## 2. Resolve Referenced Artifacts First
- Find referenced artifacts in code.
- Read minimal files to understand purpose, constraints, deps.
- Ask user only if codebase cannot answer (why, outcome, priority, hidden constraints).

## 3. Frame Current Reality
If modifying behavior:
- Document pain/failure and evidence.
- Identify what must remain unchanged.
- Check load-bearing boundaries/rules.

## 4. Goal Description
Describe problem and value. Include User Story if provided. Mention 15288:2023 transitions.

## 5. Risk Assessment (User Review Required)
Use **IMPORTANT** for architecture shifts. Use **WARNING** for breaking changes. Frame as Risk Management (15288:6.3.4).

## 6. Challenge the Fit
Verify plan is best route. Simpler path? Preserve invariants? Solve actual pain?
If weak, discuss alternatives before writing plan.

## 7. Mirror Understanding
Summarize:
- Problem & Goal
- Proposed Approach & Must-Haves (EARS)
- Invariants & Constraints
- Risks & V&V approach
- Done criteria
**Wait for explicit user confirmation before writing plan.**

## 8. Write the Plan (Proposed Changes — Design Definition)
Organize by component. Use EARS (When/While/If... shall) for each file.
Include:
- Files to modify/create and behavioral changes.
- Dependencies/ordering of changes.
- Invariants (must NOT change).

## 9. Verification Plan (V&V)
Define exact commands and expected outcomes.
- **Verification (built right):** `npm test`, lints, builds, code reviews.
- **Validation (right thing built):** End-to-end scenarios, Acceptance criteria.

## 10. Final Readiness Check
Verify:
- Problem & Goal clear.
- EARS phrasing used.
- Constraints and invariants captured.
- Testable Done criteria.
- User confirmed mirror summary first.
- Risk assessment reviewed.

</process>
