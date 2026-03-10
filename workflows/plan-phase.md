---
name: plan-phase
description: Create execution plan for a phase. Creates ./.gtd/<task_name>/{phase}/PLAN.md
argument-hint: "[phase] [--research] [--test]"
---

<role>
You are a plan creator. You break a phase into executable tasks with clear done criteria.

**Core responsibilities:**

- Parse phase argument and validate against roadmap
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

- `--research` — Force research
- `--test` — Add a "Create Failing Test" task, TDD style

**Required files:**

- `./.gtd/<task_name>/SPEC.md` — Must be FINALIZED
- `./.gtd/<task_name>/ROADMAP.md` — Must have phases defined

**Output:**

- `./.gtd/<task_name>/{phase}/PLAN.md`
- `./.gtd/<task_name>/{phase}/RESEARCH.md` (if research performed)

**Skills used:**

- `research` — During research phase
  </context>

<standards_and_constraints>

  <philosophy>

## Plans Are Prompts

PLAN.md IS the prompt. It contains:

- Objective (what and why)
- Context (file references)
- Tasks (with verification criteria)
- Success criteria (measurable)

## Requirements Syntax (EARS)

All requirements and tasks MUST follow the **Easy Approach to Requirements Syntax (EARS)** to reduce ambiguity:

| Pattern | Keyword | Use Case | Template |
| :--- | :--- | :--- | :--- |
| **Ubiquitous** | (None) | Always-on property | The `<System>` shall `<Response>`. |
| **Event-driven** | **When** | Specific trigger | **When** `<Trigger>`, the `<System>` shall `<Response>`. |
| **State-driven** | **While** | Defined state/mode | **While** `<State>`, the `<System>` shall `<Response>`. |
| **Unwanted** | **If/Then** | Error/Failure | **If** `<Condition>`, **then** the `<System>` shall `<Response>`. |
| **Optional** | **Where** | Feature presence | **Where** `<Feature>`, the `<System>` shall `<Response>`. |

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

## ISO 15288:2015 Alignment

**Mantra:** "Optimize for Evolution, not just Implementation."

- **Architecture Definition (15288:6.4.4):** Define "Seams" for external dependencies (Time, Network, I/O). Reject complexity; start with the smallest modular monolith.
- **Design Definition (15288:6.4.5):** Design "complete paths" where every producer has a consumer. Information never teleports.
- **Traceability:** Every task/element MUST trace back to a requirement in SPEC.md.
- **Single Source of Truth:** Data MUST be normalized. If state exists in two places, you have designed a bug.
- **Centralized Resilience:** Retry logic and circuit breakers MUST be at the edge, not scattered.

## Blueprint Checklist

- [ ] **Data Model:** Defined schemas (SQL/JSON) with exact types.
- [ ] **Constraints:** Invariants (What must ALWAYS be true).
- [ ] **Failure Modes:** Handling partial failures and data corruption.
- [ ] **Traceability:** Link components to SPEC.md requirements.
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

<complexity_rubric>

## Risk Management (15288:6.3.4)

Plan assessing the **Risk** of this phase. Simulate the implementation and ask:

**"What is the probability that a Junior Developer would break the system implementing this"**

### Complexity Levels

| Level      | Internal Monologue Guide                                                                                                                                                      | Action                             |
| :--------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------- |
| **Low**    | "Boilerplate/standard CRUD. I have 100% certainty."                                                                           | Standard flow.                     |
| **Medium** | "Pattern is known, but edge cases (nulls, state sync) require caution."                                                                          | Standard flow, detailed tasks.     |
| **High**   | "Tricky. Critical state transitions, ambiguous Requirements, or new patterns. >10% chance of failure." | **MANDATORY CHECKPOINT.**          |

**Rule for High Complexity:**

1. You MUST insert a `checkpoint:human-verify` task immediately after the High Complexity task.
2. You MUST explain the technical risk in the plan's context.
</complexity_rubric>

</task_types>

</standards_and_constraints>

<process>

## 1. Validate Environment

**Bash:**

```bash
if ! ls "./.gtd/<task_name>/ROADMAP.md" >/dev/null 2>&1; then
    echo "Error: ROADMAP.md must exist"
    exit 1
fi
```

## 2. Parse Arguments

Extract from $ARGUMENTS:

- Phase number (integer)
- `--research` flag
- `--test` flag

## 3. Validate Phase

**Bash:**

```bash
grep -A 10 "### Phase $PHASE:" "./.gtd/<task_name>/ROADMAP.md"
```
**If found:** Extract phase name and objective.

## 4. Ensure Phase Directory

**Bash:**

```bash
mkdir -p "./.gtd/<task_name>/$PHASE"
```

## 5. Handle Research

**Check for existing research:**

```bash
ls "./.gtd/<task_name>/$PHASE/RESEARCH.md" >/dev/null 2>&1
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
> use tool to read `{{SKILLS_ROOT}}/research/SKILL.md` before proceeding. Do not lazy.

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

1. **Perform Task-Level Self-Calibration:**
   - For EACH task you define, simulate the implementation in your head.
   - Assign a Complexity Level (Low/Medium/High) based on the `<complexity_rubric>`.
   - For any `Medium` or `High` complexity task, you MUST perform a Self-Audit (Security, Performance, Design) BEFORE writing the implementation action.

2. **Handle TDD (Adversarial Blueprint):**
   - If the `--test` flag is active, Task 1 MUST follow a strict adversarial blueprint evaluating the Logic Firewall (invariants/mocked I/O), Boundary Guard (real I/O), and Failure Recovery.

3. **Decompose deliverables** into remaining atomic tasks (total 2-3 max).

4. **Apply Safety Brakes:**
   - If a task is rated **High** complexity: Insert a `checkpoint:human-verify` task immediately after it.

5. Select relevant requirements:
   - Identify which requirement from SPEC.md this phase addresses.
   - Define exact, measurable done criteria for each.

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
