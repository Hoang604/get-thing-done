---
name: domain-truth
description: Deep-dive a single domain in a fresh conversation, confirming all [UNCONFIRMED] items via codebase exploration and user interview
disable-model-invocation: true
---

# Domain Truth Skill

Deep-dive a single domain in a fresh conversation. Read the draft from `.gtd/product/<domain>.md`, explore domain-specific code, interview the user to confirm all `[UNCONFIRMED]` items, and lock the domain truth.

---

## Continuous Background Thread

Maintain actively throughout all steps:

- **Decision Log**: After every question round, append each locked answer as one bullet under a running `## Decision Log`. All file updates are composed from this log — never from memory.
- **Reconcile Engine**: Before writing any confirmed answer, cross-reference it against:
  - Prior confirmations in this domain file.
  - `.gtd/product/index.md` cross-domain invariants.
  - `.gtd/product/glossary.md` vocabulary.

  If contradiction detected → halt with `[RECONCILE]` block: (1) the collision, (2) the trade-off, (3) forced choice with recommended resolution. Patch atomically after user selects.
- **Zero Engineering Leakage**: Restrict vocabulary to domain entities, observable outcomes, user-facing states, and system triggers.

---

## Steps

### 1. Context Load

Read the following files for context:
- `.gtd/product/index.md` — system purpose, cross-domain invariants.
- `.gtd/product/glossary.md` — locked vocabulary.
- `.gtd/product/<domain>.md` — the domain draft.

Inventory all `[UNCONFIRMED]` items and open questions from the draft.

**Completion Criterion**: All three files read. Every `[UNCONFIRMED]` item and open question catalogued.

### 2. Domain Codebase Deep-Dive

Explore domain-specific code guided by the draft's content. For each `[UNCONFIRMED]` item, classify via Confidence Horizon:

- **CONFIRMED**: Code evidence resolves it unambiguously → mark as self-resolved assumption.
- **ASKED**: Code cannot resolve it → becomes interview question.
- **SELF-RESOLVED**: Unambiguous convention or default → mark as assumption.

Identify additional workflows, rules, and edge cases not in the draft.

**Completion Criterion**: Every `[UNCONFIRMED]` item classified. All discovered additions compiled.

### 3. Interactive Domain Interview

Use `ask_question` to resolve all ASKED items and newly discovered ambiguities.

**Progressive Building**: Update `.gtd/product/<domain>.md` section-by-section as the user confirms. Remove `[UNCONFIRMED]` markers on confirmed items.

**Glossary Proposals**: If a new domain term needs locking, propose it via `ask_question`. On user approval, append to `.gtd/product/glossary.md` with status `[PROPOSED]`.

**Structured Natural Language Guidance**: Business rules should follow a consistent pattern for clarity, e.g.:
> When \<trigger\>, the system guarantees \<outcome\>. If \<failure\>, then \<fallback\>.

This is guidance for consistency, not enforced syntax.

**Completion Criterion**: Domain entropy = 0. Zero `[UNCONFIRMED]` items or open questions remaining.

### 4. Structural Coherence Check

Lightweight audit of the confirmed domain file:

- **Dangling references**: Every referenced entity, state, or workflow is defined.
- **Missing fallbacks**: Every workflow where failure is possible has an error policy.
- **Internal contradictions**: No two rules conflict within the domain.
- **Cross-domain alignment**: No contradiction with `index.md` invariants.

If gaps found → return to Step 3 for targeted interview.

**Completion Criterion**: Zero structural gaps detected.

### 5. Publish & Hand-off

Remove the Open Questions section from `<domain>.md`.

Output: `[DOMAIN CONFIRMED] — <domain> truth locked in .gtd/product/<domain>.md`

**Completion Criterion**: File contains only confirmed content with zero `[UNCONFIRMED]` markers. Hand-off delivered.

---

## Edge Cases

- **Re-run on confirmed domain**: Treat existing confirmed content as ground truth. Interview only about gaps or changes.
- **Domain boundary shift**: If content belongs to a different domain, flag it for the user. Do not modify other domain files.
- **Glossary conflict**: If a proposed term conflicts with an existing glossary entry, raise `[RECONCILE]` with forced choice.
