---
name: req-to-tickets
description: Break any raw requirement directly into tickets, each sized for 1 plan in /draft-plan
disable-model-invocation: true
---

# Req to Tickets (`Direct Requirement-to-Ticket Decomposition`)

Decompose **any raw requirement** (prompt, issue description, conversation context, bug report, or feature request) directly into an actionable dependency graph of **tracer-bullet vertical slice tickets** without requiring an intermediate `SPEC.md`.

Each ticket is sized and scoped so that it maps cleanly to **one concrete plan** to be drafted via `/draft-plan`.

---

## Process

### 1. Ingest Requirement & Establish Task Scope

1. Ingest the raw requirement from the user prompt, arguments, issue, or conversation context.
2. Determine or derive a concise `<task_name>` (kebab-case, e.g., `auth-jwt`, `rate-limiter`).
3. Ensure directory `./.gtd/<task_name>/tickets/` is designated for ticket publication.

---

### 2. Codebase Seam Exploration (`Mandatory Legwork`)

You MUST explore the codebase to bridge requirement concepts into exact technical boundaries before drafting tickets.

#### A. Seam Mapping
- Run `grep_search` and `list_dir` to locate implementation files (`controllers, services, models/schemas, types, config`) relevant to the requirement.
- Identify conventions and existing patterns in the repository.

#### B. Prefactor & Structural Bottleneck Audit
- Identify tightly coupled modules, hardcoded assumptions, or legacy structures that block a clean implementation.
- Schedule any identified structural blocker as an explicit **Prefactor Ticket** (`executed before feature slices`).
- If a change touches shared symbols across $> 5$ files, sequence it via **Expand–Contract** (Expand ticket → Batch migration tickets → Contract ticket).

#### C. Completion Criterion
Do not draft tickets until you have established a clear internal **Seam Mapping Matrix**:
`[Requirement Concept / Entity] -> [Target Files / Symbols] -> [Required Prefactors / Invariants]`

---

### 3. Decompose into Vertical Slice Tickets (`draft-plan Sizing Contract`)

Break the work into tickets where **each ticket is scoped to be executed as 1 single plan in `/draft-plan`**:

- **Slice Scope (1 Ticket = 1 Plan):** Each ticket must fit in a single fresh context window (`<= 5 primary seams/files`).
- **Flexible Blast Radius:** Identify core targets and openly document anticipated related files (callers, schemas, mappers, downstream consumers). Avoid rigidly freezing file boundaries so real implementation can adapt naturally.
- **Vertical Slice:** Each ticket cuts through all necessary layers (`schema, domain logic, API/wiring`) so it is independently verifiable.
- **Dependencies:** Declare explicit `Blocked by` identifiers (`<NN> — <Title>` or `None — can start immediately`).

---

### 4. Publish Tickets

Write one file per ticket under `./.gtd/<task_name>/tickets/<NN>-<slug>.md`, numbered from `01` in dependency order (`blockers first`).

Use `<ticket-template>` below — one ticket per file, never a combined file:

<ticket-template>

# <NN> — <Ticket title>

- **Primary Targets:** [<primary_file_1>](file:///path), [<primary_file_2>](file:///path)
- **Anticipated Blast Radius:** [<related_file_1>](file:///path), [<related_file_2>](file:///path)
- **Blocked by:** `<NN> — <Title>` or `None — can start immediately`
- **Status:** `ready-for-agent`
<!-- Guidance: Anticipated Blast Radius contains only clickable markdown file links of potential callers, schemas, mappers, or downstream consumers. Do not output literal guidance text or test references. -->

## Context & What to Build
Explain in direct, conversational technical language (explain-style: senior engineer over coffee):
- **Current System**: Architecture, runtime environment, and current data flow.
- **What to Build & Fit**: The end-to-end capability this ticket delivers, exactly where it plugs into the broader system, and clear scope boundaries (in-scope vs deferred to subsequent tickets).

## Acceptance criteria
- [ ] When <event / input trigger>, system <expected behavior>
  - **Expected Outcome:** <Exact payload, DB state, or UI/log change>
- [ ] If <invalid condition / error>, system <expected handling>
  - **Expected Outcome:** <Error code, message displayed, or rejected state>
... (List all applicable behaviors and invariants for this slice)

> **Execution Note for Agent:**
> Do not assume automated test suites or invent test files. Verify code statically (syntax, types, interface wiring). Do not hallucinate runtime verification (such as claiming curl was run when no server was active); provide the exact expected outcome so the user can test and accept.

</ticket-template>

---

### 5. Output Summary & Next Action

Display a concise summary table of the published tickets and guide the user on the next action:

```markdown
### Tickets Published (`./.gtd/<task_name>/tickets/`)

| Ticket | Blocked by |
|---|---|
| [01 — <Ticket Title>](file:///absolute/path/to/.gtd/<task_name>/tickets/01-<slug>.md) | None — can start immediately |
| [02 — <Ticket Title>](file:///absolute/path/to/.gtd/<task_name>/tickets/02-<slug>.md) | 01 — <Ticket Title> |

**Next step:** Pick an unblocked frontier ticket (e.g., ticket `01`) and run `/draft-plan` to create its implementation plan.
```
