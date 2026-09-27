---
name: product-interview
description: "Stage 3: Interactive domain interview grounded in codebase exploration to establish a comprehensive product draft."
disable-model-invocation: true
---

## Prime Directive

The sole success criterion: you and the user hold the exact same understanding of what needs to be done before any work begins. Grounded in `docs/proposals/<feature>/proposal.md` and `docs/proposals/<feature>/codebase-trace.md`, resolve all structural gaps, unhandled states, and policy ambiguities to produce an authoritative product specification draft: `docs/proposals/<feature>/product-draft.md`.

---

## The Continuous Background Thread

Maintain actively throughout execution:

- **Zero Hallucination**: Extract requirements and facts exclusively from explicit user confirmations and verified codebase findings. Never invent domain rules or assume unstated business logic.
- **Zero Engineering Leakage**: Express all specifications strictly in human domain language, strictly excluding implementation symbols and syntax.
- **Context Air-Gap Invariant**: The Main Agent must never inspect source code files or execute code searches. Codebase exploration is quarantined entirely within the `codebase-tracer` subagent.
- **Grounded System Reality**: The verified objective operational truth actively enforced by the existing system. All domain specifications must anchor strictly to this reality without assuming unbuilt capabilities or violating system boundaries.
- **Semantic Sync**: Propose precise Working Definitions for newly introduced domain nouns and verbs, locking on user confirmation.
- **Reconcile Engine**: Before writing any confirmed answer to disk, cross-reference it against:
  - `docs/proposals/<feature>/proposal.md`
  - `docs/proposals/<feature>/codebase-trace.md`
  - Prior confirmations in this session.
  If a contradiction is detected, halt with a `[RECONCILE]` block: (1) the collision, (2) the trade-off, (3) forced choice with recommended resolution. Patch atomically after the user selects.
- **Decision Log**: After every question round, append each newly locked answer as one bullet under a running `## Decision Log`, echoed in chat. The draft MUST be composed exclusively from this log — never from memory.

---

## Execution Steps

### 1. Codebase Trace (Subagent) & Gap Inventory

1. **Spawn Codebase Tracer**: Invoke `codebase-tracer` via `invoke_subagent` passing exclusively:
   `Target proposal: <absolute_path_to_proposal>`
   Completion criterion: The subagent completes execution and emits `docs/proposals/<feature>/codebase-trace.md`.
2. **Ingest Baseline Assets**: Read `docs/proposals/<feature>/proposal.md` and `docs/proposals/<feature>/codebase-trace.md` using `view_file`.
3. **Contrast Scan**: Contrast the proposal against grounded system reality documented in `codebase-trace.md`. Identify every ambiguity, contradiction, or unhandled reality where an implementing engineer would otherwise be forced to guess or invent business behavior.
4. **Compile Inventory**: Compile these into an inventory of load-bearing unknowns, ordered by dependency: resolve foundational choices that reshape the problem before probing dependent details.
- **Completion Criterion**: `codebase-trace.md` exists on disk, and the inventory of load-bearing unknowns is established in memory.

### 2. Relentless Interview

Use the `ask_question` tool to resolve every load-bearing unknown in the inventory:
- **Grounded Question**: Open by articulating the grounded system reality that blocks or conflicts with the proposal and why engineering cannot resolve it without a business policy decision, then pose the domain choice.
- **Operational Options**: Pair every question with 2–3 concrete choices, `(Recommended)` first, formatted as the user's direct response. Define each choice as an operational mechanism rather than an action label:
  `<Operational Mechanism> — Choose this if <Trade-off>`
- Use `is_multi_select: true` when multiple independent choices or constraints can be selected simultaneously.
- **Stopping Rule**: Halt questioning when every finding in the inventory has an explicit domain resolution locked in the Decision Log.

### 3. Multi-Tab Playback Gate

When all inventory questions are resolved, synthesize the findings and invoke `ask_question` with 4 self-contained tabs (`questions: [...]`):

1. **Goal & Flow** (`is_multi_select: false`):
   - `question`: "### 1. Goal & Observable Flow\n- **Goal**: <1-2 sentences>\n- **User Flow**: <step-by-step actions and outcomes>\n\nIs the goal and flow accurate?"
   - `options`: `["(Recommended) Confirmed — exact goal and user flow", "Goal or user flow needs adjustment"]`
2. **Scope & Invariants** (`is_multi_select: false`):
   - `question`: "### 2. Scope & Invariants\n- **In Scope**: <features to build>\n- **Out of Scope**: <deferred/excluded>\n- **Core Invariants**: <conservation laws and business immutabilities>\n\nAre scope and invariants correct?"
   - `options`: `["(Recommended) Confirmed — scope and invariants are solid", "Scope or invariants need revision"]`
3. **State Transitions & Degradation** (`is_multi_select: false`):
   - `question`: "### 3. State Transitions & Degradation\n- **States & Transitions**: <valid state graph>\n- **Error Policies & Fallbacks**: <degradation behaviors and liability>\n\nDoes the lifecycle design match?"
   - `options`: `["(Recommended) Confirmed — lifecycle and fallbacks are correct", "Lifecycle or fallbacks need changes"]`
4. **Assumptions & Open Items** (`is_multi_select: true`):
   - `question`: "### 4. Assumptions & Open Items\n- **Assumption 1**: <first assumption>\n- **Assumption 2**: <second assumption>\n\nWhich items need adjustment?"
   - `options`: `["(Recommended) None — all assumptions confirmed", "Veto Assumption 1", "Veto Assumption 2"]`

If any tab is flagged or assumption vetoed, re-probe only the disputed dimension via Step 2, update the Decision Log, and re-issue the gate.

### 4. Emit Product Draft

When the user confirms all tabs of the Multi-Tab Playback Gate, write the authoritative domain specification directly to the file `docs/proposals/<feature>/product-draft.md`.
- Must be composed exclusively from the confirmed Decision Log and grounded system reality.
- Express all contracts strictly in human domain language and tables. Exclude implementation code blocks and programming language syntax.
- Present all confirmed decisions using whatever structure and style best communicates the target domain behavior.
- **Completion Criterion**: The file `docs/proposals/<feature>/product-draft.md` exists on disk reflecting all confirmed decisions from the Playback Gate, with zero unconfirmed markers.

Direct the user to open a fresh conversation and invoke `entropy-hunt` as the next step.
