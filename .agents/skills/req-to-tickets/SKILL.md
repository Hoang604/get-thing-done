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

- **Slice Scope (1 Ticket = 1 Plan):** Each ticket must fit in a single fresh context window (`<= 5 core seams/files`).
- **Vertical Slice:** Each ticket cuts through all necessary layers (`schema, logic, API, tests`) so it is independently verifiable.
- **Dependencies:** Declare explicit `Blocked by` identifiers (`<NN> — <Title>` or `None — can start immediately`).

---

### 4. Publish Tickets

Write one file per ticket under `./.gtd/<task_name>/tickets/<NN>-<slug>.md`, numbered from `01` in dependency order (`blockers first`).

Use `<ticket-template>` below — one ticket per file, never a combined file:

<ticket-template>

# <NN> — <Ticket title>

**Seam Targets:** `[basename.ext](file:///absolute/path/to/basename.ext)`
**Blocked by:** `<NN> — <Title>` or `None — can start immediately`
**Status:** `ready-for-agent`

## What to build
The end-to-end behavior or capability this ticket makes work from the user/caller perspective. Clearly define what is in scope and what is deferred to subsequent tickets.

## Acceptance criteria
- [ ] `[REQ-01]` `[EARS format: Ubiquitous / Event / State / Unwanted / Optional]` → **Proof:** `[Exact observable state/response/test to verify]`
- [ ] `[REQ-02]` `[EARS format: Ubiquitous / Event / State / Unwanted / Optional]` → **Proof:** `[Exact observable state/response/test to verify]`
... (List all specific acceptance criteria for this slice)

</ticket-template>

---

### 5. Output Summary & Next Action

Display a concise summary table of the published tickets and guide the user on the next action:

```markdown
### Tickets Published (`./.gtd/<task_name>/tickets/`)

| # | Ticket Title | Blocked by | Target Seams |
|---|---|---|---|
| 01 | <Prefactor or First Slice> | None | `[file.py](file:///path)` |
| 02 | <Next Slice> | 01 | `[service.py](file:///path)` |

**Next step:** Pick an unblocked frontier ticket (e.g., ticket `01`) and run `/draft-plan` to create its implementation plan.
```
