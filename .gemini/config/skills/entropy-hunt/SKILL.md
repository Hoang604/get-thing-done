---
name: entropy-hunt
description: "Stage 4: Adversarially audit product draft against codebase reality via air-gapped subagent to lock zero-entropy product specification."
disable-model-invocation: true
---

## Prime Directive

The sole criterion: an engineer can implement the entire feature without ever having to pause and ask the business side for missing details or clarification.

Execution is strictly divided into two air-gapped stages:
1. **Codebase Reality Audit (Subagent)**: Quarantines codebase investigation to emit technical audit findings to `brain/`.
2. **Domain Resolution (Main Agent)**: Operates strictly on air-gapped domain inputs to resolve business trade-offs with the user.

Iterate across versions (`product-spec-v<N>.md`) with strict drift prevention. When a walkthrough surfaces zero questions, freeze the final specification as `docs/proposals/<feature>/product-spec-locked.md` with status `[ENTROPY = 0: LOCKED]`.

---

## The Continuous Background Thread

Maintain actively throughout execution:

- **Context Air-Gap Invariant**: The Main Agent must never inspect source code files. Codebase exploration is quarantined entirely within the Subagent.
- **Zero-Code Domain Invariant**: All interactions with the user must be confined exclusively to domain semantics, devoid of engineering leakage.
- **Anti-Drift Verbatim Invariant**: Every new version `product-spec-v<N>.md` must preserve the exact text of `v<N-1>`, appending newly locked policies or atomically patching only explicitly modified sections. Never paraphrase or rewrite established text from memory.
- **Decision Log**: After every question round, append each locked policy as one bullet under a running `## Decision Log`, echoed in chat. The specification must be composed exclusively from this log.
- **Reconcile Engine**: Before locking any answer, cross-reference it against existing platform invariants and prior confirmations. If a contradiction is detected, halt with a `[RECONCILE]` block to force a clear trade-off.

---

## Execution Steps

### 1. Ingest Latest Baseline

Locate the latest specification file on disk:
- If no `docs/proposals/<feature>/product-spec-v*.md` exists, read `docs/proposals/<feature>/product-draft.md` (baseline for `v1`).
- Otherwise, read the highest version `docs/proposals/<feature>/product-spec-v<N-1>.md` (baseline for `v<N>`).

### 2. Stage 1: Codebase Reality Audit (Subagent)

Spawn `codebase-auditor` via `invoke_subagent` passing exclusively this prompt with zero additions:
`Target specification: <absolute_path_to_spec>`

Completion criterion: The subagent completes execution and emits its audit artifact.

### 3. Stage 2: Domain Resolution (Main Agent)

Read the audit artifact emitted by the subagent using `view_file`.

If unresolved items exist in the audit artifact, invoke `ask_question`:
- **Grounded Question**: Open by articulating the codebase reality that blocks the specification and why engineering cannot resolve it without a business policy decision, then pose the domain choice.
- **Operational Options**: Pair every question with 2–3 concrete choices, `(Recommended)` first, formatted as user's direct response. Define each choice as an operational mechanism rather than an action label:
  `<Operational Mechanism> — Choose this if <Trade-off>`
- Stopping Rule: Halt questioning when every finding in the audit artifact has an explicit domain resolution.

### 4. Emit Version or Lock

- **If questions were resolved in this run**:
  1. Write `docs/proposals/<feature>/product-spec-v<N>.md` by taking `v<N-1>` verbatim and applying newly confirmed policies from the Decision Log.
  2. Direct the user to open a fresh conversation and re-run `entropy-hunt` on this latest version.
- **If zero questions were surfaced in the walkthrough (Terminal Convergence)**:
  1. Write the final specification directly to `docs/proposals/<feature>/product-spec-locked.md`.
  2. Add the terminal verification header: `[ENTROPY = 0: LOCKED]`.
  3. Output terminal confirmation:
     `[SPEC LOCKED] — Specification complete. An engineer can implement without asking business details.`

- **Completion Criterion**: If unknowns existed, `product-spec-v<N>.md` exists on disk reflecting newly confirmed policies without text drift, with the user directed to continue in a fresh conversation. If zero unknowns remained, `product-spec-locked.md` exists on disk with status `[ENTROPY = 0: LOCKED]`. Hand-off delivered.
