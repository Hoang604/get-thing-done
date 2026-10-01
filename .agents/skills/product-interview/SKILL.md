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
- **Semantic Sync**: Propose precise Working Definitions for newly introduced domain nouns and verbs, locking on user confirmation.
- **Reconcile Engine**: Before writing any confirmed answer to disk, cross-reference it against:
  - `docs/proposals/<feature>/proposal.md`
  - `docs/proposals/<feature>/codebase-trace.md`
  - Prior confirmations in this session.
  If a contradiction is detected, halt with a `[RECONCILE]` block: (1) the collision, (2) the trade-off, (3) forced choice with recommended resolution. Patch atomically after the user selects.
- **Decision Log**: After every question round, append each newly locked answer as one bullet under a running `## Decision Log`, echoed in chat. The draft MUST be composed exclusively from this log — never from memory.

---

## Execution Steps

### 1. Gap Inventory & Contrast Scan

Contrast `docs/proposals/<feature>/proposal.md` against `docs/proposals/<feature>/codebase-trace.md`.
Identify every ambiguity, contradiction, or unhandled reality where an implementing engineer would otherwise be forced to guess or invent business behavior.

Compile these into an inventory of load-bearing unknowns, ordered by dependency: resolve foundational choices that reshape the problem before probing dependent details.

### 2. Relentless Interview

Use the `ask_question` tool to resolve every load-bearing unknown in the inventory:
- Formulate each question around a concrete business decision that eliminates developer guesswork.
- Pair every question with 2–3 concrete choices, plus one pre-calculated `(Recommended)` default listed first. Format options as the user's direct response.
- **Decision-Framed Options**: Format every option as: `<User Action / Business Choice> — Choose this if <condition>`.
- Use `is_multi_select: true` when multiple independent choices or constraints can be selected simultaneously.

Halt questioning when zero points of developer guesswork remain between the proposal and codebase reality, and all decisions are locked in the Decision Log.

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
- Must be composed exclusively from the confirmed Decision Log and verified code assets.
- Present all confirmed decisions using whatever structure and style best communicates the target domain behavior.
- **Completion Criterion**: The file `docs/proposals/<feature>/product-draft.md` exists on disk reflecting all confirmed decisions from the Playback Gate, with zero unconfirmed markers.

Direct the user to open a fresh conversation and invoke `entropy-hunt` as the next step.
