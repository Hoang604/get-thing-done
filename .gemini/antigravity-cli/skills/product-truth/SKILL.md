---
name: product-truth
description: Investigate codebase and interview user to establish ground truth product specification across domains in .gtd/product/
disable-model-invocation: true
---

# Product Truth Skill

Investigate the codebase, identify domain boundaries, and interview the user to establish an authoritative ground truth specification in `.gtd/product/` — system-level overview, cross-domain vocabulary, and per-domain drafts prepared for `domain-truth`.

---

## Continuous Background Thread

Maintain actively throughout all steps:

- **Decision Log**: After every question round, append each locked answer as one bullet under a running `## Decision Log`, echoed in chat. All output files are composed exclusively from this log — never from memory.
- **Reconcile Engine**: Before writing any confirmed answer to disk, cross-reference it against all previously written sections across all output files. If contradiction detected, halt with a `[RECONCILE]` block: (1) the collision, (2) the trade-off, (3) forced choice with recommended resolution. Patch atomically after user selects.
- **Zero Engineering Leakage**: Restrict all output vocabulary to domain entities, observable outcomes, user-facing states, and system triggers. No class names, function signatures, or code topology.

---

## Steps

### 1. Codebase Exploration & Domain Discovery

Explore the codebase to understand:
- **System Purpose & Target Consumers**: Who interacts with the system.
- **Bounded Contexts**: Identify natural domain boundaries — module clusters, data ownership, independent workflows.
- **Cross-Domain Workflows**: Map operations that span multiple domains.
- **Ambiguous Vocabulary**: Tag overloaded or ambiguous domain nouns for Semantic Sync.

**Completion Criterion**: Working inventory compiled — every identified domain named and bounded, ambiguous terms tagged, cross-domain workflows traced.

### 2. System-Level Interview & Glossary Lock

Interview the user via `ask_question` to resolve system-level concerns:
- System purpose and target users.
- Domain boundaries — names, ownership, relationships.
- Cross-domain invariants and workflows.
- **Semantic Sync**: For every ambiguous or overloaded term, propose a precise Working Definition. Lock the meaning on user confirmation.

**Progressive Building**: As each section is confirmed, immediately write it to `.gtd/product/index.md` or `.gtd/product/glossary.md`.

**Auto-Locking**: When the user confirms domain boundaries, lock minor intra-domain details to recommended defaults for the drafts.

**Completion Criterion**: Domain entropy = 0 at system level. All cross-domain concerns confirmed and written to disk. Every ambiguous term locked in `glossary.md`.

### 3. Domain Deep-Dive & Draft Preparation

For each identified domain: thorough codebase exploration of domain-specific code. Extract workflows, business rules, error policies. Mark all findings `[UNCONFIRMED]`. Compile specific open questions for `domain-truth` to resolve.

Write each `.gtd/product/<domain>.md` draft progressively as domains are explored.

**Completion Criterion**: Every domain has a partially-filled draft with identified workflows, inferred business rules, open questions, and `[UNCONFIRMED]` markers on all domain-specific content.

### 4. Publish & Hand-off

Verify all files are on disk conforming to their schemas:
- `.gtd/product/index.md`
- `.gtd/product/glossary.md`
- `.gtd/product/<domain>.md` for each domain

Output hand-off listing each domain and its draft status. Direct the user to invoke `domain-truth` with each domain name in a fresh conversation.

**Completion Criterion**: All files exist conforming to schemas. Hand-off delivered.

---

## Output Schemas

### `index.md` — `.gtd/product/index.md`

```markdown
# Product Truth: System Overview

## 1. System Purpose & Target Users
- **Primary Users / Consumers**: <who>
- **Core Problem Solved**: <what>

## 2. Domain Map
| Domain | File | Description | Status |
|---|---|---|---|
| <name> | [<name>.md](./name.md) | <1-line description> | Draft |

## 3. Cross-Domain Invariants
- **<Invariant Name>**: <rule that spans domain boundaries>

## 4. Cross-Domain Workflows
### <Workflow Name>
- **Domains Involved**: <domain-a>, <domain-b>
- **Flow**: <step-by-step across domain boundaries>
- **Expected Outcome**: <observable result>
```

### `glossary.md` — `.gtd/product/glossary.md`

```markdown
# Domain Vocabulary

Locked Working Definitions for terms shared across domains or with overloaded meaning.

| Term | Working Definition | Source Domain(s) | Status |
|---|---|---|---|
| <term> | <precise, unambiguous definition> | <domain(s)> | Locked |
```

### `<domain>.md` — `.gtd/product/<domain>.md`

```markdown
# Domain: <Domain Name>

## 1. Domain Purpose
- **Bounded Context**: <what this domain owns>
- **Key Entities**: <primary domain objects>

## 2. User Workflows & Expected Outcomes
### <Workflow Name> [UNCONFIRMED]
- **User Intent**: <what the user aims to accomplish>
- **Expected Outcome**: <concrete, observable result>
- **Feedback & Guarantees**: <what the user sees, state guaranteed>

## 3. Business Rules & Invariants
- **<Rule Name>** [UNCONFIRMED]: <e.g. When <trigger>, the system guarantees <outcome>. If <failure>, then <fallback>.>

## 4. Error Policies & Edge Cases
- **<Error Scenario>** [UNCONFIRMED]: <expected behavior, fallback, or error message>

## 5. Open Questions
- <Specific ambiguity or gap for domain-truth to resolve>
```
