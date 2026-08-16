---
name: to-tickets
description: Break a ./.gtd/<task_name>/SPEC.md to a set of tickets
disable-model-invocation: true
---

# To Tickets (`Domain-to-Seam Decomposition`)

Convert a verified `./.gtd/<task_name>/SPEC.md` (`WHAT/WHY`) into an actionable dependency graph of **tracer-bullet vertical slice tickets** (`WHERE/HOW`) by exploring the codebase and declaring explicit **blocking edges**.

## Process

### 1. Gather Context & Domain Grounding

Read the provided `./.gtd/<task_name>/SPEC.md` (`and any related conversation context or reference passed as arguments`).
- Extract all confirmed EARS requirements, error fallbacks, and the sequential `Execution Roadmap`.

### 2. Codebase Seam & Prefactor Exploration (`Mandatory Legwork`)

You MUST explore the codebase to bridge the `SPEC.md` domain concepts into exact technical boundaries before drafting any tickets.

#### A. Mechanical Seam Mapping (`Trace Entities to Code`)
- Run `grep_search` and `list_dir` to locate the exact implementation files (`controllers, services, models/schemas, types`) corresponding to every confirmed entity and EARS requirement in `SPEC.md`.
- Verify architectural guidelines by checking existing `ADRs` or project conventions in the repository.

#### B. Prefactor & Blast Radius Audit (`Make the Change Easy`)
- Inspect call sites and structural dependencies of the identified seams.
- **Structural Bottleneck Check:** Identify tightly coupled modules, hardcoded assumptions, or legacy structures that would block a clean implementation. Every identified bottleneck MUST be scheduled as an explicit **Prefactor Ticket** (`executed before feature slices`).
- **Wide Refactor Check:** If a required change touches shared symbols across $> 5$ files (`Wide Blast Radius`), mark it for **Expand-Contract** sequencing (`Step 3`).

#### C. Completion Criterion (`Seam & Prefactor Matrix`)
Do not proceed to `Step 3` until you have established a clear **Seam Mapping Matrix** internally (`[Domain Entity/Rule] -> [Exact Target Files/Modules] -> [Required Prefactor/ADR Constraints]`). Every drafted ticket title and description MUST strictly employ the repository's existing codebase vocabulary (`e.g., class/package names`) rather than generic prose.

### 3. Draft Vertical Slices (`Tracer Bullet Contract`)

Break the work into **tracer bullet** tickets strictly grounded in your `Seam Mapping Matrix`.

<vertical-slice-rules>

- **Roadmap Alignment:** Each drafted feature ticket MUST correspond precisely to a roadmap phase from `SPEC.md` (`or an independently verifiable sub-slice of a phase if the phase touches multiple distinct technical seams`).
- **Slice Anatomy:** Each slice cuts a narrow but COMPLETE path through every layer (`schema, API, UI, tests`) — vertical, NOT a horizontal layer-by-layer slice. A completed slice MUST be independently demoable or `Black-Box Verifiable`.
- **Sizing:** Size each ticket to fit in a single fresh context window (`<= 5 core seams/files when implemented`). Any identified prefactor tickets must be scheduled first, blocking the core feature tickets.

</vertical-slice-rules>

Assign explicit **blocking edges** (`Blocked by`) to every ticket. A ticket with no blockers can start immediately.

**Wide Refactor Exception:** Sequence wide mechanical refactors via **Expand–Contract**:
1. **Expand Ticket:** Add the new form beside the old (`blocked by any prefactor`).
2. **Migrate Batches:** Migrate call sites in batches sized by blast radius (`per package/dir`), each batch blocked by the `Expand Ticket`, keeping CI green batch-to-batch.
3. **Contract Ticket:** Delete the old form once zero callers remain, blocked by `Every Migrate Batch`.

#### Exhaustive Slicing Check (`Step 3 Completion Criterion`)
Before moving to `Step 4`, verify your drafted ticket graph strictly satisfies:
- **100% Roadmap Coverage:** Every single phase from `SPEC.md Execution Roadmap` and every mandatory `Prefactor Seam` from `Step 2` is explicitly accounted for by at least one drafted ticket.
- **Zero EARS Omission (`No Lossy Summarization`):** Every EARS requirement and error fallback extracted from `SPEC.md` during `Step 1` MUST be explicitly mapped 1:1 to the Acceptance Criteria of at least one drafted ticket. Never summarize multiple EARS rules into a single generic bullet.
- **Zero Orphaned Edges:** Every drafted ticket declares exact `Blocked by` identifiers or `None — can start immediately`.

### 4. Quiz the User (`Interactive Review Gate`)

Present the proposed breakdown as a concise numbered list. For each ticket, display strictly:
- **Title**: short descriptive name using codebase vocabulary (`e.g., [BillingLedger] Add retry fallbacks`)
- **Blocked by**: which other tickets (`if any`) must complete first
- **Target Seams**: exact files/modules identified during `Step 2`
- **EARS Rules Covered**: exact compact list of rule IDs/origins mapped to this slice (`e.g., [Phase 2: EARS-3, EARS-4 + Fallback-1]`)
- **What it delivers**: the observable `Black-Box Verifiable` value delivered

Conclude the display with a proactive assessment and a single clear action request:

```markdown
**Agent Assessment:**
- *Granularity & Edges:* All tickets fit within 1 PR scope. `[State any identified coupling risks or recommended execution ordering explicitly]`.
- *EARS Coverage:* 100% of confirmed EARS rules (`Rule ID range + Fallbacks`) accounted for across the ticket graph.

**Action Required:** Does this breakdown feel right? Type `Approve` to publish files to `./.gtd/<task_name>/tickets/` or specify adjustments.
```

Iterate until the user explicitly approves the breakdown.

### 5. Publish the Tickets

Write one file per ticket under `./.gtd/<task_name>/tickets/<NN>-<slug>.md`, numbered from `01` in dependency order (`blockers first`). Each file's `Blocked by` lists the numbers/titles it depends on. Use `<ticket-template>` below — one ticket per file, never a single combined file.

Work the **frontier**: any ticket whose blockers are all completed (`"None — can start immediately"`).

Do NOT close or modify any parent issue or specification.

<ticket-template>

# <NN> — <Ticket title>

**Seam Targets:** `[basename.py](file:///absolute/path/to/basename.py)` (`or specific module names`)
**Blocked by:** `<NN> — <Title>` or `None — can start immediately`
**Status:** `ready-for-agent`

## What to build
The end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list. Grounded in `./.gtd/<task_name>/SPEC.md`.

## Acceptance criteria

<criteria-mapping-rules>
- **Exhaustive EARS Extraction:** List EVERY confirmed EARS requirement (`PRECONDITION, WHEN, WHILE`), state invariant, and error fallback from `./.gtd/<task_name>/SPEC.md` that falls within this ticket's seam boundaries. Do not truncate to fit a fixed number of bullets.
- **Traceability:** Prefix each criterion with its exact `SPEC.md` origin (`e.g., [Phase 2 — EARS-3]`).
- **Observable Proof:** Every criterion MUST append an explicit `Black-Box Proof` (`the exact API status code, DB row state, log emitted, or UI element change required to prove completion`).
</criteria-mapping-rules>

- [ ] `[SPEC.md Origin]` `[EXACT EARS RULE: PRECONDITION / WHEN / IF ... THEN ...]` → **Proof:** `[Exact observable state/response to verify]`
- [ ] `[SPEC.md Origin]` `[EXACT EARS RULE: PRECONDITION / WHEN / IF ... THEN ...]` → **Proof:** `[Exact observable state/response to verify]`
... (`Repeat exhaustively for all applicable rules in this slice`)

</ticket-template>

Avoid massive code snippets — they go stale fast. Exception: prototype snippets (`state machine, reducer, type shape`) may be inlined if trimmed to decision-rich parts.
