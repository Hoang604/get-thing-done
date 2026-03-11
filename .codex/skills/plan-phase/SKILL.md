---
name: plan-phase
description: Create execution plan for a phase. Creates ./.gtd/<task_name>/{phase}/PLAN.md. User manually trigger, do not auto invoke this.
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

If deep research is needed, summarize first:

1. From `ROADMAP.md`: phase name, objective, dependencies
2. From `SPEC.md`: relevant Must Have and Nice To Have requirements
3. Scope boundaries: in-scope vs out-of-scope files/modules
Then run:

spawn_agent({ agent_type: "worker", message: "
<objective>
Research Phase {N}: {phase_name} well enough to support writing PLAN.md.
</objective>

<context>
Task: <task_name>
Phase directory: ./.gtd/<task_name>/$PHASE/
Authoritative inputs:
- ./.gtd/<task_name>/SPEC.md
- ./.gtd/<task_name>/ROADMAP.md

Relevant phase details:
- Objective: {phase_objective}
- Dependencies: {phase_dependencies}
- Relevant Must Haves: {must_have_requirements}
- Relevant Nice To Haves: {nice_to_have_requirements}
- Scope boundaries: {in_scope_and_out_of_scope}
</context>

<deliverable>
Write your findings to:
./.gtd/<task_name>/$PHASE/RESEARCH.md
</deliverable>

<research_questions>
1. Which files/modules are most relevant to this phase?
2. What existing patterns or abstractions should be reused?
3. What constraints, edge cases, or risks could affect planning?
4. What testing seams or dependency boundaries are available?
5. What file-level scope should PLAN.md reference explicitly?
</research_questions>

<rules>
- Do not modify source code.
- Do not write PLAN.md.
- Keep findings concrete and planning-focused.
- If something is uncertain, state the uncertainty clearly.
</rules>

<return_to_caller>
Return only a short summary with:
- key modules
- major constraints
- main risks
- recommended file scope for the plan
</return_to_caller>
"})
wait({ ids: ["<agent_id>"] })

Read ./.gtd/<task_name>/$PHASE/RESEARCH.md before continuing.
---

## 6. Create Plan

Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► PLANNING PHASE {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
### 6a. Gather Context

Read `SPEC.md`, `ROADMAP.md`, and `RESEARCH.md` (if present). Use them to define scope, constraints, and requirement coverage for
this phase.

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

{How will we verify this phase meets requirements}

## Spec Requirements (Traceability)

<!-- List the specific requirements from SPEC.md that this phase addresses -->
- [ ] Must Have: {Requirement 1}
- [ ] Nice To Have: {Requirement 2}

## Context

- ./.gtd/<task_name>/SPEC.md
- ./.gtd/<task_name>/ROADMAP.md
- {relevant source files}

## Architecture Constraints

- **Single Source:** {Where is the authoritative data?}
- **Invariants:** {What must ALWAYS be true?}
- **Decision Rationale:** {Why this architectural choice was made}
- **Testability:** {What needs to be injected/mocked (Design Seams)}

## Tasks

<!-- All tasks and 'done' criteria MUST use EARS keywords where applicable -->

<!-- If --test flag IS SET, inject the slot. If NOT set, use standard Task 1 -->
{{#if test_flag}}
<task id="1" type="auto" complexity="Null">
  <!-- TDD_STRATEGY_SLOT -->
</task>
{{else}}
<task id="1" type="auto" complexity="Low/Medium/High">
  <name>{Task name}</name>
  <risk>{One sentence rationale if complexity > Low}</risk>
  <files>{exact related file paths}</files>
  <requirement>
    **When** {Trigger}, the {System} shall {Action}.
  </requirement>
  <action>
    {Exact sequence of agent tool calls / code edits}
    - Modify {file} to implement {logic}
  </action>
  <done>{How we know this task is complete}</done>
</task>
{{/if}}

<task id="2" type="checkpoint:human-verify">
  <name>STOP. Review the implementation of {file} for {specific_risk}</name>
  <risk>{One sentence rationale if complexity > Low}</risk>
  <files>{exact related file paths}</files>
  <action>
    {Specific review instructions}
  </action>
  <done>{How we know this task is complete}</done>
</task>

<task id="3" type="auto">
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
- [ ] Adherence to `<critical_rules>`

**If issues found:** Fix before finishing.

---

## 8. Enhance Plan (TDD)

**If `--test` flag is active:**

Display:

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► DESIGNING TDD STRATEGY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Use a subagent for test strategy:

```text
spawn_agent({ agent_type: "test_strategist", message: "
<objective>
Design a comprehensive TDD strategy for Phase {N}: {phase_name}.
Replace Task 1 in PLAN.md with rigorous specification-based tests.
</objective>

<context>
  <plan_file>./.gtd/<task_name>/{N}/PLAN.md</plan_file>
  <spec_file>./.gtd/<task_name>/SPEC.md</spec_file>
  <roadmap_file>./.gtd/<task_name>/ROADMAP.md</roadmap_file>
  <research_file>./.gtd/<task_name>/{N}/RESEARCH.md</research_file>
</context>

<focus>
1. Verify SPEC.md requirements are covered.
2. Ensure strict separation of Logic (Unit) vs I/O (Integration).
3. Identify and attack fragile logic paths.
</focus>
"})
wait({ ids: ["<agent_id>"] })
```

Apply the returned strategy into `PLAN.md`.

---

## 9. Review Plan (Conditional)

**If ANY task has complexity = Medium or High, you MUST:**

Use a review subagent:

```text
spawn_agent({ agent_type: "review_plan", message: "
<scope>./.gtd/<task_name>/{N}/PLAN.md</scope>

<objective>
Review for security, performance, logic flaws, and design risks before execution
</objective>

<context>
## Phase Context
Phase {N}: {phase_name}
Goal: {phase objective}

## Tasks to Review (Medium/High Complexity)
- Task {id}: {name} - Complexity: {level}
  Risk: {why this needs review}

## Architecture Constraints
- {key constraints from SPEC that apply}
</context>

<focus_areas>security, performance, logic, design</focus_areas>
<output_format>Status: BLOCK | CAUTION | PROCEED, plus findings</output_format>
"})
wait({ ids: ["<agent_id>"] })
```

**If STATUS: BLOCK** → Revise plan before proceeding.
**If STATUS: CAUTION** → Note risks in plan, proceed with awareness.
**If STATUS: PROCEED** → Continue to offer next step.

**If ALL tasks are Low complexity:** Skip review, proceed directly.

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
$execute {N} — run this plan
─────────────────────────────────────────────────────
Also available:
$discuss-plan {N} — review plan before executing
─────────────────────────────────────────────────────
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
