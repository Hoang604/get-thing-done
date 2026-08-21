---
name: product-truth
description: Investigate codebase and interview user via ask_question to establish ground truth business invariants and user outcomes in .gtd/PRODUCT.md.
disable-model-invocation: true
---

# Product Truth Skill

Investigate the codebase, identify domain ambiguities, and interview the user via `ask_question` to establish an authoritative ground truth specification in `./.gtd/PRODUCT.md`.

---

## Steps

### 1. Codebase Exploration & Ambiguity Discovery
Explore the codebase to understand:
- **System Purpose & Target Consumers**: Identify who interacts with the system (end users, admins, developers, external services).
- **Core User Workflows**: Map the primary operations users perform and their expected outcomes.
- **Business Rules & State Invariants**: Trace domain logic, data transformations, and state constraints.
- **Implicit Assumptions & Edge Cases**: Identify unhandled branches, conflicting logic, or unconfirmed business policies.

**Completion Criterion**: Working inventory of identified workflows, inferred business rules, and specific clarification questions compiled.

### 2. Interactive Invariant & Outcome Resolution
Interview the user exclusively via the `ask_question` tool to resolve all identified ambiguities:
- Clarify target user personas and their expected outcomes for core workflows.
- Confirm strict business invariants and permission boundaries.
- Define expected system behaviors for edge cases and failure modes.

**Completion Criterion**: Zero unconfirmed business rules or ambiguous user outcomes remaining.

### 3. Publish Product Truth
Write `./.gtd/PRODUCT.md` conforming to the **Product Truth Schema**.

**Completion Criterion**: `./.gtd/PRODUCT.md` exists and contains confirmed system purpose, user expected outcomes, business invariants, and error policies.

---

## Product Truth Schema (`.gtd/PRODUCT.md`)

```markdown
# Product Truth Specification

## 1. System Purpose & Target Users
- **Primary Users / Consumers**: <Who uses or integrates with this system>
- **Core Problem Solved**: <The primary job-to-be-done and value delivered>

## 2. User Expected Outcomes & Core Workflows
- **<Workflow / Action Name>**:
  - User Intent: <What the user aims to accomplish>
  - Expected Outcome: <Concrete, observable result upon success>
  - Feedback & Guarantees: <What the user sees and what state is guaranteed>

## 3. Business Rules & Invariants
- **Rule 1**: <Uncompromising invariant that code must uphold at all times>
- **Rule 2**: <Uncompromising invariant that code must uphold at all times>

## 4. Error Policies & Edge Cases
- **<Error Scenario / Edge Case>**: <Expected system behavior, fallback, or error message presented to user>
```
