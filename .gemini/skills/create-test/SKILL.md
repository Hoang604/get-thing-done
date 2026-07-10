---
name: create-test
description: Design repo-specific test strategy and write deterministic tests catching real boundary and invariant bugs at clean external seams
disable-model-invocation: true
---

# CORE DIRECTIVE

Investigate target code to discover actual invariants, boundary contracts, and failure seams.
Design adversarial tests that catch regression mutations (`Breaks-If`). Never mirror implementation logic or write tautology tests.

**Seam Discipline (`Replace, Don't Layer & Anti-Brittle Defense`):**
- **The Interface is the Test Surface (`Signature + Invariants + Error Modes`):** An interface is *everything* a caller must know to use the module (`type signature, invariants, ordering constraints, error modes`), not just the API signature. Callers and tests cross this exact same **External Seam**. Never test *past* the interface by asserting on private methods, internal state, or intermediate call graphs. If a test breaks when internal implementation refactors while external behavior remains identical, it is a brittle implementation-coupled test (`Test Rác`) and is strictly rejected.
- **Dependency Categorization & Mocking Ban (`DEPENDING discipline`):**
  1. `In-process` (pure compute, in-memory state): **Strictly forbid mocks.** Merge modules and test directly through the interface.
  2. `Local-substitutable` (Postgres, Filesystem): **Strictly forbid mocks.** Test using real local stand-ins (`PGLite`, `tmp_path`, in-memory DB).
  3. `Remote-owned` (Internal microservices): Define a port (`seam`); test via `In-Memory Adapter` (`FakePort`).
  4. `True-external` (Stripe, Twilio): Only here are mock/stub adapters permitted.

---

## Phase 1: CONFIRM (`Investigation & Test Plan Proposal`)

Perform exhaustive **Legwork** on the target (`module, file, function, interface`) to map observable inputs, outputs, side effects, dependency categories, and error handling. Detect existing test framework conventions (`runner, assertion style, stand-in patterns`).

Do not write or modify any test code during Phase 1. Present the concrete **Test Strategy Proposal** and wait for explicit user approval:

### A. Seam & Dependency Audit (`Anti-Brittle Verification`)
- **Target Seam / Interface:** State exactly the external interface signature to be tested (`e.g., [OrderService.place_order](file:///path#L20)`). Confirm that no private helper or internal seam is exposed solely for testing (`Zero Interface Leakage`).
- **Dependency Map & Test Stand-in:** Categorize every dependency of the target (`In-process`, `Local-substitutable`, `Remote-owned`, `True-external`) and specify the exact stand-in or adapter used (`e.g., Postgres -> Local PGLite stand-in; DiscountCalc -> In-process direct call; Stripe -> Mock Adapter`).

### B. Oracle Declaration (`Ground Truth vs Assumptions`)
- **Behavioral & Boundary Claims:** Cite exact sources (`e.g., CLAIM: Order status locks after payment -> SOURCE: [OrderService.py:L45](file:///path#L45)` or `SPEC`).
- **Causal Independence:** State exact variables that must not alter outputs (`e.g., sort order must not affect total calculation`).
- **Unverified Assumptions:** Explicitly flag any untraced claims with `⚠️ ASSUMPTION — needs human confirmation`.

### C. Test Matrix (`Adversarial & Invariant Focus`)
For each test item, verify that it asserts on observable interface behavior (`Observable Outcome`) and declare its failure trigger (`Breaks-If Mutation`). Reject any item whose failure condition is "internal method called differently":

| Test Category | Target Seam / Function | Verification Target (`Observable Outcome / Invariant`) | Test Stand-in / Adapter (`No In-Process Mocks`) | Breaks-If Mutation (`Specific Code Bug That Fails This`) |
| :--- | :--- | :--- | :--- | :--- |
| **Unit / Logic** | `[calc_total](file:///path#L10)` | Total == Sum(items) - discount | `In-process direct call` | Omitting discount clamp when total < 0 |
| **Integration** | `[process_pay](file:///path#L50)` | Database rollback on timeout | `Local stand-in (PGLite/SQLite)` | Swallowing timeout exception without rollback |
| **Adversarial** | `[parse_header](file:///path#L20)` | Rejection of truncated/bad payload | `In-process direct call` | Accepting malformed payload header |
| **Edge Case** | `[init_pool](file:///path#L5)` | Graceful failure when pool_size=0 | `In-memory FakePort` | Division by zero or unhandled IndexError |

**Hard Stop:** Output exactly: `Please review the proposed test matrix and assumptions. I will not write test code until explicitly confirmed.`

---

## Phase 2: EXECUTE (`Test Implementation & Mechanical Proof`)

Upon user confirmation, execute the test strategy:
1. **Write Test Code:** Create or modify test files following exact workspace structure and naming (`*.test.ts`, `test_*.py`). Strictly enforce **The Interface is the Test Surface** — zero assertions on internal implementation structures.
2. **Mark Unverified Oracles:** If any `⚠️ ASSUMPTION` remained unverified, attach an inline comment: `# ⚠️ UNVERIFIED ORACLE: <reason>`.
3. **Mechanical Proof:** Run the exact test command against the new tests (`e.g., uv run pytest <filepath>`, `npm test <filepath>`) and output the raw pass/fail summary.
