---
name: arch-to-tickets
description: Decompose an ARCHITECTURE.md blueprint into an actionable dependency graph of vertical slice tickets sized for draft-plan
disable-model-invocation: true
---

# CORE DIRECTIVE

Convert a verified `./.gtd/<task_name>/ARCHITECTURE.md` blueprint into an actionable dependency graph of tracer-bullet vertical slice tickets.

Preserve all structural contracts, state transition guarantees, and failure perimeters defined in the blueprint. Enforce bidirectional reconciliation: if codebase reality refutes any architectural assumption, update `ARCHITECTURE.md` directly at the root cause before issuing tickets.

Each ticket is sized and scoped to execute as one concrete plan in `/draft-plan`.

---

## 1. Ingest Blueprint & Scope Verification

1. Derive the task identifier denoted as `<task_name>` from user arguments, active context, or existing `.gtd/` directory structure.
2. Read `./.gtd/<task_name>/ARCHITECTURE.md` using `view_file`.
3. Confirm that the directory `./.gtd/<task_name>/tickets/` is designated for ticket publication.

- **Completion Criterion**: `ARCHITECTURE.md` ingested and verified intact.

---

## 2. Codebase Grounding & Bidirectional Reconciliation

Ground the blueprint against physical repository reality before drafting tickets.

### Reconciliation Invariant

An architecture blueprint provides macro-level direction. Grounding it against codebase reality may expose unworkable boundaries or flawed assumptions.

- **Contract Ingestion:** Established signatures, schemas, and state transitions that align with codebase reality are ingested directly into ticket contracts without lossy paraphrasing.
- **Root-Cause Synchronization:** If codebase grounding reveals that repository reality refutes any assumption in the blueprint, forbid downstream ad-hoc workarounds in tickets. Update `./.gtd/<task_name>/ARCHITECTURE.md` directly to resolve the defect at the root cause, preserving the blueprint as the authoritative single source of truth before issuing tickets.

- **Completion Criterion**: Physical target files located, symbols verified against the codebase, and any required architectural corrections committed directly to `ARCHITECTURE.md`.

---

## 3. Decompose into Vertical Slice Tickets

Break the architecture into tracer-bullet tickets where **each ticket is scoped to execute as 1 single plan in `/draft-plan`**:

### Slicing Principles

- **Vertical Slice Contract:** Each ticket cuts through all necessary layers to deliver an independently verifiable capability. Avoid horizontal layer-by-layer slicing.
- **Sizing Scope:** Center each ticket around a focused primary core (`<= 5` primary seams). Distinguish primary targets from anticipated blast radius callers to allow realistic execution adjustments.
- **Dependency Graph:** Assign explicit blocking identifiers (`Blocked by: <NN> — <Title>` or `Blocked by: None — can start immediately`). A ticket with no blockers represents an unblocked frontier that can begin immediately.
- **Zero Orphaned Architecture:** Every boundary seam, data schema, and state transition defined in `ARCHITECTURE.md` must be accounted for across the ticket graph.

---

## 4. Ticket Construction Contract

Publish one file per ticket under `./.gtd/<task_name>/tickets/<NN>-<slug>.md`, numbered from `01` in dependency order.

Use `<ticket-template>` below:

<ticket-template>

# <NN> — <Ticket title>

- **Primary Targets:** [<primary_file_1>](file:///path), [<primary_file_2>](file:///path)
- **Anticipated Blast Radius:** [<related_file_1>](file:///path), [<related_file_2>](file:///path)
- **Blocked by:** `<NN> — <Title>` or `None — can start immediately`
- **Status:** `ready-for-agent`

## Context & What to Build
Explain in direct, conversational technical language (explain-style: senior engineer over coffee):
- **Current System**: Architecture, runtime environment, and current data flow.
- **What to Build & Fit**: The end-to-end capability this ticket delivers, exactly where it plugs into the broader subsystem, and clear scope boundaries (in-scope versus deferred to subsequent tickets). Grounded in `./.gtd/<task_name>/ARCHITECTURE.md`.

## Architectural Seams & Literal Contracts
- **Architectural Seams Covered:** Citing target symbols, ports, and interface signatures from `ARCHITECTURE.md`.
- **Governed State Transitions:** Declaring current state, trigger, next state, and enforced invariants from the blueprint state matrix.

## Acceptance criteria
- [ ] When <event / input trigger>, system <expected behavior>
  - **Expected Outcome:** <Exact payload, state mutation, or return value>
- [ ] If <invalid condition / failure state>, system <expected handling>
  - **Expected Outcome:** <Exact error type, recovery behavior, or rejected state>

> **Execution Note for Agent:**
> Do not assume automated test suites or invent test files. Verify code statically (syntax, types, interface wiring). Do not hallucinate runtime verification; provide the exact expected outcome so the user can test and accept.

</ticket-template>

---

## 5. Output Summary & Next Action

Display a concise summary table of published tickets and guide the user on the next action:

```markdown
### Tickets Published (`./.gtd/<task_name>/tickets/`)

| Ticket | Blocked by |
|---|---|
| [01 — <Title>](file:///absolute/path/to/.gtd/<task_name>/tickets/01-<slug>.md) | None — can start immediately |
| [02 — <Title>](file:///absolute/path/to/.gtd/<task_name>/tickets/02-<slug>.md) | 01 — <Title> |

**Next step:** Pick an unblocked frontier ticket (e.g., ticket `01`) and run `/draft-plan` to create its implementation plan.
```

Stop calling tools or generating text.
