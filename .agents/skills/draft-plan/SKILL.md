---
name: draft-plan
description: Draft plan after confirm approach
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved alignment contract or propose plan into a deterministic, zero-entropy `implementation_plan.md` Artifact.
Do not re-explore alternative designs. Enforce literal interface boundaries (`class` / `def` signatures with docstrings and type annotations) paired with explicit inline contracts (`invariants, error modes, data structures`). Never leak method bodies or line-by-line implementation code into the plan. Enforce independent subagent code verification to guarantee exhaustive execution without failure-hiding.

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

Translate approved requirements strictly into checkable EARS syntax structures:

- [ ] **Ubiquitous:** `The <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **Event:** `When <Trigger>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **State:** `While <State>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **Unwanted:** `If <Condition>, then the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **Optional:** `Where <Feature>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)

**Zero Orphan Requirements & Pipeline Tracing:** Every single requirement must explicitly cite the exact clickable markdown link (`file://` with line anchor if modifying, or target path if new) of the target seam/interface that fulfills it (e.g., `-> Fulfills at [OrderService.process_order](file:///path/service.py#L45)`). For changes to intermediate pipeline stages, annotate the upstream ingress and downstream terminal sink (e.g., `-> Ingress: [API.route](file:///path#L10) | Egress: [DB.persist](file:///path#L80)`).

---

## 3. Affected Files

List all files that will be created, modified, or deleted by this plan in a structured file tree format inside a text block.

```tree
.
├── src/
│   ├── [NEW] api/routes.py
│   └── [MODIFY] main.py
└── config/
    └── [MODIFY] settings.json
```

---

## 4. Design Definition (`Zero-Prose Literal Contracts & Seam Matrix`)

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

---

## 5. Verification & Validation Proof

Define mechanical, checkable proof of completion across the seam:

### A. Baseline Check & Subagent Audit
- **Baseline Check:** Run exact terminal commands (`e.g.,` typecheck, lints, builds, smoke tests) executing against the target interfaces.
  - **Pipeline Gate:** When modifying intermediate pipeline stages, verification commands MUST execute the pipeline integration/E2E suite from ingress to terminal sink; isolated unit tests on the intermediate seam alone are strictly insufficient.
- **Independent Subagent Audit:** After running verification commands, spawn a dedicated verification subagent via `invoke_subagent`:
  1. **Tool Restriction:** Subagent uses `view_file` only; runs no commands.
  2. **Subagent Prompt:** Send all EARS requirements verbatim and instruct the subagent to view the codebase to evaluate completeness. It must start from the file cited at `-> Fulfills at [TargetSeam]` for each requirement, but is not bound to only that file.
  3. **Standardized Subagent Output:** For each requirement, the subagent must output strictly:
     - `REQ: <verbatim requirement>` -> `PASS | FAIL`
     - `<Concise rationale citing lines viewed>`

### B. Remediation Loop
- For all requirements marked `FAIL`:
  1. Form the approach to do it right.
  2. Apply the fix in the code.
  3. Spawn the verification subagent again to verify.
  4. Repeat until all requirements are marked `PASS`.

### C. Completion Criteria (Mandatory Delivery Gate)
To finalize execution and declare completion, the agent MUST embed the completed subagent audit table directly inside `#### 2. Verification Proof` of the `Execution & Verification Report`:

```markdown
#### 2. Verification Proof
- **Baseline Check:** `<Exact command(s) executed for verification>` -> `<Passing output summary line / exit code>`
- **Subagent Audit Proof (Auditor ID: `<Conversation ID>`):**
  | # | EARS Requirement | Subagent Status | Line Citations |
  |---|---|---|---|
  | REQ-01 | `<Verbatim requirement>` | PASS / FAIL | [file:line](file:///...) |
```

Execution is strictly INCOMPLETE if any row in the Audit Table has status `FAIL` or is missing.
