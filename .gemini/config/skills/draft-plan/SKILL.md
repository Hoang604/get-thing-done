---
name: draft-plan
description: Draft plan after confirm approach
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved alignment contract or propose plan into a deterministic, zero-entropy `implementation_plan.md` Artifact.
Do not re-explore alternative designs. Enforce literal interface boundaries (`class` / `def` signatures with docstrings and type annotations) paired with explicit inline contracts (`invariants, error modes, data structures`). Never leak method bodies or line-by-line implementation code into the plan.

---

## 1. User Outcome & Risk Assessment

- Copy the exact **User Outcomes** block finalized and approved during alignment (`propose-plan` or `confirm`).
- Use GitHub-style alerts strictly to flag architectural boundaries and risks:
  - `> [!CAUTION]` for architecture shifts or data loss risks.
  - `> [!WARNING]` for breaking changes to public APIs or schemas.
  - `> [!IMPORTANT]` for critical load-bearing boundaries and invariants.
  - `> [!NOTE]` for minor side effects or operational gotchas.

---

## 2. Requirements (EARS Syntax & Seam Tracing)

Translate approved requirements strictly into EARS syntax structures:

- **Ubiquitous:** `The <system/component> shall <Action>.`
- **Event:** `When <Trigger>, the <system/component> shall <Action>.`
- **State:** `While <State>, the <system/component> shall <Action>.`
- **Unwanted:** `If <Condition>, then the <system/component> shall <Action>.`
- **Optional:** `Where <Feature>, the <system/component> shall <Action>.`

**Zero Orphan Requirements & Pipeline Tracing:** Every single EARS requirement must explicitly cite the exact clickable markdown link (`file://` with line anchor if modifying, or target path if new) of the target seam/interface that fulfills it (e.g., `-> Fulfills at [OrderService.process_order](file:///path/service.py#L45)`). For changes to intermediate pipeline stages, annotate the upstream ingress and downstream terminal sink (e.g., `-> Ingress: [API.route](file:///path#L10) | Egress: [DB.persist](file:///path#L80)`).

---

## 3. Affected Files

List all files that will be created, modified, or deleted by this plan in a structured file tree format inside a text block.

```tree
.
├── src/
│   ├── [NEW] api/routes.py
│   └── [MODIFY] main.py
└── tests/
    └── [DELETE] test_old.py
```

---

## 4. Design Definition (`Zero-Prose Literal Contracts & Seam Matrix`)

### A. Literal Interface Contracts (`Signatures, Schemas & Inline Seam Contracts`)

For every target file to create (`[NEW]`), modify (`[MODIFY]`), or delete (`[DELETE]`), pinpoint exact line ranges using clickable [basename](file:///path#L10-L20) links without backticks and declare exact literal contracts:

- **Target Seam, Signatures & Data Schemas (`Literal Signatures, Types & DTOs`):**
  - Write ONLY the exact external boundary (`class` / `def` signatures, Pydantic/dataclass fields, TypedDicts, Enums, or config tables) with complete docstrings and strict type annotations (`e.g., def process(self, context: SpeechContext) -> None: """...""" ...`).
  - Declare all explicit data structures (input/output models, payload schemas, DB migrations/tables) crossing the boundary. Always use `...` (ellipses) to represent method bodies. If complex logic, explain in docstrings.
- **Ordered Execution Pipeline & State Transitions:**
  - Define a concise, numbered sequential flow and state transitions within the seam (e.g., `1. Validate idempotency token -> 2. Acquire lock -> 3. Mutate ledger -> 4. Emit event`).
  - Explicitly mark atomic transaction boundaries and rollback semantics without leaking line-by-line implementation code.
- **Exact Caller & Downstream Sink Audit (`grep_search & dataflow proof`):**
  - **Caller Audit (Upstream Ingress):** Run `grep_search` across the workspace for this symbol. List every single caller file and exact line range (e.g., [caller.py:L10-L25](file:///path/caller.py#L10-L25)) that must be updated to match the new signature. If 0 callers exist outside tests, state: `"Caller Audit: 0 production callers found via grep_search."`
  - **Sink Audit (Downstream Dataflow):** For intermediate pipeline stages, trace the return values, payload mutations, or emitted events downstream until reaching a **Terminal Sink** (HTTP response, persistent store, external queue, or UI render). List every downstream consumer (e.g., [consumer.py:L50-L70](file:///path/consumer.py#L50-L70)) and verify schema compatibility. If this seam is itself the terminal boundary, state: `"Sink Audit: Terminal sink reached at this seam."`
  - **Composition & Runtime Wiring:** Specify exact registration points where the new or modified seam is instantiated, registered, or mounted in the application lifecycle (e.g., DI container, route mounting in server, CLI subcommands).
- **Invariants, Concurrency & Error Modes:**
  - State exact invariants (`what must not change`), exact typed exceptions raised (`exceptions/return variants`), concurrency controls (locks, mutexes, thread safety), AND flag any out-of-seam state accessed directly (`e.g., os.environ keys or config tables read without parameter injection`).

### B. Adversarial Seam & Test Replacement Matrix (`Replace, Don't Layer & Anti-Brittle Defense`) (Optional)

> [!NOTE]
> **Optional Section:** Only write this section and test matrix if the user explicitly said they want tests. If tests were not explicitly requested by the user, omit this subsection completely from the plan.

The interface is the test surface (`Signature + Invariants + Error Modes`). Callers and tests cross the exact same external seam. Strictly reject brittle tests that assert on private methods, internal state, or intermediate call graphs (`e.g., toHaveBeenCalledWith`).

When tests are explicitly requested, define deep adversarial test specifications across 4 categories (`Unit/Logic`, `Integration`, `Adversarial`, `Edge Case`) for each affected seam:

| Test Category | Target Seam / Module | Old Shallow Test to [DELETE] | New Deep Test & Observable Invariant | Dependency Category & Test Stand-in | Breaks-If Mutation (Specific Code Bug That Fails This) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unit / Logic** | [Order.calc_total](file:///path#L10) | [test_old.py:L10](file:///path#L10) or None | [test_order.py:L15](file:///path#L15): Total == sum(items) - discount | `In-process direct call` | Omitting discount clamp when total < 0 |
| **Integration** | [OrderService.pay](file:///path#L50) | [test_old.py:L40](file:///path#L40) or None | [test_order_svc.py:L30](file:///path#L30): DB rollback on gateway timeout | `Local stand-in (PGLite/SQLite)` | Swallowing timeout exception without rollback |
| **Adversarial** | [OrderParser.parse](file:///path#L20) | None | [test_parser.py:L10](file:///path#L10): Explicit rejection of malformed payload | `In-process direct call` | Accepting malformed payload header |
| **Edge Case** | [Pool.acquire](file:///path#L5) | None | [test_pool.py:L20](file:///path#L20): Graceful failure when pool_size=0 | `In-memory FakePort` | Division by zero or unhandled IndexError |

- **Seam & Dependency Discipline (`DEPENDING discipline`):**
  1. `In-process` (pure compute, in-memory state): Strictly forbid mocks. Merge modules and test directly through the interface.
  2. `Local-substitutable` (Postgres, filesystem): Strictly forbid mocks. Use real local stand-ins (`PGLite`, `tmp_path`, in-memory DB).
  3. `Remote-owned` (Internal microservices): Define a port (`seam`); test via `In-Memory Adapter` (`FakePort`).
  4. `True-external` (Stripe, Twilio): Mock/stub adapters permitted.
- **Oracle Declarations & Causal Independence:**
  - **Ground Truth:** Cite exact source for every claim (`SPEC` or `SOURCE: [file:line]`). Flag unverified claims with `⚠️ ASSUMPTION`.
  - **Causal Independence:** Explicitly declare variables that must not alter outputs (e.g., list order, cache hits/misses).
- **No Interface Leakage:** Never expose private helper methods or internal seams solely for unit test setup. Tests must assert on observable outcomes strictly through the module's external seam.

---

## 5. Verification & Validation Proof

Define mechanical, checkable proof of completion across the seam:

- **Verification Commands:** Exact terminal commands (`e.g., uv run pytest <target_test_file>`, `npm test`, lints, builds) executing against the target interfaces.
  - **Pipeline Gate:** When modifying intermediate pipeline stages, verification commands MUST execute the pipeline integration/E2E suite from ingress to terminal sink; isolated unit tests on the intermediate seam alone are strictly insufficient.
- **Validation Scenarios:** Step-by-step observable acceptance criteria or end-to-end user flows to verify success.
