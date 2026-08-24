---
name: test-increment
description: Design adversarial test seams and update implementation plan
disable-model-invocation: true
---

# CORE DIRECTIVE

Ingest the active `implementation_plan.md` Artifact and any user-provided directives to formulate deterministic, adversarial test seams.
Design adversarial tests that catch regression mutations (`Breaks-If`). Never mirror implementation logic or write tautology tests.
Refine and update Section 4.B (`### B. Adversarial Seam & Test Replacement Matrix`) of the `implementation_plan.md` Artifact.

**Source of Truth Hierarchy:**
1. **User Directives (Absolute Priority):** Any information, invariants, test cases, or constraints provided directly by the user in the prompt or conversation are binding **Ground Truth**. They override any inferred assumptions or default conventions.
2. **Implementation Plan:** Sections 1 through 4.A of `implementation_plan.md` serve as the pre-audited baseline. Do not re-scan callers, re-explore system architecture, or re-scan tests already identified in the plan.

**Seam Discipline (`Replace, Don't Layer & Anti-Brittle Defense`):**
- **The Interface is the Test Surface (`Signature + Invariants + Error Modes`):** An interface is *everything* a caller must know to use the module (`type signature, invariants, ordering constraints, error modes`), not just the API signature. Callers and tests cross this exact same **External Seam**. Never test *past* the interface by asserting on private methods, internal state, or intermediate call graphs (`e.g., toHaveBeenCalledWith`). If a test breaks when internal implementation refactors while external behavior remains identical, it is a brittle implementation-coupled test (`Test Rác`) and is strictly rejected.
- **Dependency Categorization & Mocking Ban (`DEPENDING discipline`):**
  1. `In-process` (pure compute, in-memory state): **Strictly forbid mocks.** Merge modules and test directly through the interface.
  2. `Local-substitutable` (Postgres, Filesystem): **Strictly forbid mocks.** Test using real local stand-ins (`PGLite`, `tmp_path`, in-memory DB).
  3. `Remote-owned` (Internal microservices): Define a port (`seam`); test via `In-Memory Adapter` (`FakePort`).
  4. `True-external` (Stripe, Twilio): Only here are mock/stub adapters permitted.

---

## Phase 1: CONFIRM (`Adversarial Seam Matrix Proposal`)

Read `implementation_plan.md` and incorporate any additional user-provided instructions. Formulate the concrete adversarial test matrix directly from the plan's interface contracts without performing redundant codebase scans.

Present the concrete **Test Seam Proposal** and wait for explicit user approval:

### A. Seam & Dependency Audit (`Anti-Brittle Verification`)
- **Target Seam / Interface:** State exactly the external interface signature to be tested from the plan (`e.g., [OrderService.place_order](file:///path#L20)`). Confirm zero internal/private interface leakage.
- **Dependency Map & Test Stand-in:** Categorize every dependency of the target (`In-process`, `Local-substitutable`, `Remote-owned`, `True-external`) and specify the exact stand-in or adapter used.

### B. Oracle Declaration (`Ground Truth vs Assumptions`)
- **Behavioral & Boundary Claims:** Cite exact sources (`e.g., USER PROMPT`, `SPEC`, or `SOURCE: [OrderService.py:L45](file:///path#L45)`).
- **Causal Independence:** State exact variables that must not alter outputs (`e.g., sort order must not affect total calculation`, `cache hit/miss must not change return payload`).
- **Unverified Assumptions:** Explicitly flag any untraced claims with `⚠️ ASSUMPTION — needs human confirmation`.

### C. Adversarial Test Matrix (`Invariant & Mutation Focus`)
For each test item across the 4 mandatory categories (`Unit / Logic`, `Integration`, `Adversarial`, `Edge Case`), verify observable interface behavior and declare its failure trigger (`Breaks-If Mutation`). Reject any item whose failure condition is "internal method called differently":

| Test Category | Target Seam / Module | Old Shallow Test to [DELETE] | New Deep Test & Observable Invariant | Dependency Category & Test Stand-in | Breaks-If Mutation (Specific Code Bug That Fails This) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unit / Logic** | `[Order.calc_total](file:///path#L10)` | `[test_old.py:L10](file:///path#L10)` or None | `[test_order.py:L15](file:///path#L15)`: Total == sum(items) - discount | `In-process direct call` | Omitting discount clamp when total < 0 |
| **Integration** | `[OrderService.pay](file:///path#L50)` | `[test_old.py:L40](file:///path#L40)` or None | `[test_order_svc.py:L30](file:///path#L30)`: DB rollback on gateway timeout | `Local stand-in (PGLite/SQLite)` | Swallowing timeout exception without rollback |
| **Adversarial** | `[OrderParser.parse](file:///path#L20)` | None | `[test_parser.py:L10](file:///path#L10)`: Explicit rejection of malformed payload | `In-process direct call` | Accepting malformed payload header |
| **Edge Case** | `[Pool.acquire](file:///path#L5)` | None | `[test_pool.py:L20](file:///path#L20)`: Graceful failure when pool_size=0 | `In-memory FakePort` | Division by zero or unhandled IndexError |

**Hard Stop:** Output exactly: `Please review the proposed adversarial test matrix and assumptions. I will not update the implementation plan until explicitly confirmed.`

---

## Phase 2: EXECUTE (`Plan Artifact Update`)

Upon explicit user confirmation:
1. **Update Artifact:** Modify the `implementation_plan.md` Artifact in place. Replace Section 4.B with the approved **Adversarial Seam & Test Replacement Matrix**, seam discipline rules, and oracle citations.
2. **Synchronize Proof Commands:** Ensure Section 5 (`Verification & Validation Proof`) in `implementation_plan.md` contains the exact verification commands (`e.g., uv run pytest <filepath>`, `npm test <filepath>`) targeting the newly defined test seams.
3. **Report Update:** Present a concise summary of the refined test seams added to the plan and prompt: `"Implementation plan test seams updated. Click Proceed button or run /execute to proceed with implementation."`
