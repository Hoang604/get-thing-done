---
name: draft-plan
description: Draft plan after confirm approach
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved alignment contract or propose plan into a deterministic, zero-entropy `implementation_plan.md` Artifact.
Do not re-explore alternative designs. Enforce literal interface boundaries (`class` / `def` signatures with docstrings and type annotations) paired with explicit inline contracts (`invariants, error modes, data structures`). Never leak method bodies or line-by-line implementation code into the plan. Enforce independent subagent code verification to guarantee exhaustive execution without failure-hiding.

---

## 1. User Outcomes & Risk Assessment

### User Outcomes
Translate the approved **User Outcomes** from alignment (`propose-plan` or `confirm`) into trackable items with unique IDs. Each outcome declares what capability or quality is delivered, how completion is verified, and where to look:

- [ ] **UO-01:** <Clear capability or quality statement>
  - **Acceptance Signal:** <How do we know this is done? Observable output / metric / structural property>
  - **Verification Scope:** <Where to look — file path(s), entry→exit flow, or measurement method>
- [ ] **UO-02:** ...

### Risk Assessment
Use GitHub-style alerts strictly to flag architectural boundaries and risks:
  - `> [!CAUTION]` for architecture shifts or data loss risks.
  - `> [!WARNING]` for breaking changes to public APIs or schemas.
  - `> [!IMPORTANT]` for critical load-bearing boundaries and invariants.
  - `> [!NOTE]` for minor side effects or operational gotchas.

---

## 2. Requirements (EARS Syntax & Seam Tracing)

Translate approved requirements strictly into checkable EARS syntax structures. Each requirement MUST include a **`[UO-xx]` traceability tag** linking it back to the User Outcome it serves:

- [ ] **REQ-01 [UO-01] (Ubiquitous):** `The <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-02 [UO-01] (Event):** `When <Trigger>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-03 [UO-02] (State):** `While <State>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-04 [UO-01] (Unwanted):** `If <Condition>, then the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-05 [UO-02] (Optional):** `Where <Feature>, the <system/component> shall <Action>.` -> Fulfills at [TargetSeam](file:///path#L10)

**Zero Orphan Requirements & Bidirectional Tracing:** Every requirement must (a) explicitly cite the exact clickable markdown link (`file://` with line anchor if modifying, or target path if new) of the target seam/interface that fulfills it (e.g., `-> Fulfills at [OrderService.process_order](file:///path/service.py#L45)`), AND (b) trace back to at least one User Outcome via the `[UO-xx]` tag. For changes to intermediate pipeline stages, annotate the upstream ingress and downstream terminal sink (e.g., `-> Ingress: [API.route](file:///path#L10) | Egress: [DB.persist](file:///path#L80)`). Every `UO-xx` must be served by at least one `REQ-yy`; orphan outcomes are plan defects.

---

## 3. Affected Files

### Scope Discovery
Starting from each UO's Verification Scope and each REQ's Fulfills-at target, trace callers and consumers outward using `grep_search` and `view_file`. At each hop, determine whether the file requires changes to fulfill the plan. If yes, add it to the manifest and trace its callers/consumers in turn.

**Fixed-point criterion:** Scope discovery is complete when an additional trace hop produces no new files requiring changes.

### File Manifest

```tree
.
├── src/
│   ├── [NEW] api/routes.py          # UO-01 scope trace
│   ├── [MODIFY] service.py          # REQ-01 fulfills-at
│   └── [MODIFY] main.py             # service.py caller hop
└── config/
    └── [MODIFY] settings.json       # REQ-03 fulfills-at
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

In `implementation_plan.md`, define the mechanical, checkable verification steps that the executing agent must perform upon completing code changes:

### A. Baseline Check
- Specify exact terminal commands (`e.g.,` typecheck, lints, builds, smoke tests) executing against the target interfaces.

### B. Independent Subagent Dual Audit & Exact Spawn Prompt
The plan MUST define the exact subagent invocation and the literal, fully rendered prompt that the executing agent will use.

> [!IMPORTANT]
> The plan defines the execution instructions and the literal spawn prompt. The executing agent MUST NOT paraphrase, summarize, or abbreviate this prompt during invocation. Real audit results must come exclusively from the live subagent execution.

The plan must instruct the executing agent to follow these exact steps:

1. **Subagent Invocation Configuration:**
   - Tool: `invoke_subagent`
   - `TypeName`: `"research"`
   - `Role`: `"Outcome & Requirements Auditor"`
   - **Tool Restriction:** Subagent uses `view_file` only; runs NO commands.

2. **Literal Spawn Prompt Block:**
   The plan must write out the exact prompt string for the subagent, embedding all User Outcomes verbatim from Section 1 AND all EARS requirements verbatim from Section 2:

   ````markdown
   #### Subagent Spawn Directive
   > [!CAUTION]
   > **LITERAL INVOCATION REQUIRED**: When invoking the auditor subagent, copy the entire block below character-for-character into the `invoke_subagent` `Prompt` argument. Do not summarize, translate or rephrase.

   ```text
   You are an independent Outcome & Requirements Auditor. Your sole mission is dual verification: verifying both micro-level technical requirements AND macro-level end-to-end user outcomes in the implemented code.

   1. User Outcomes to verify:
   - [ ] UO-01: <Verbatim capability/quality statement from Section 1>
     - Acceptance Signal: <Verbatim from Section 1>
     - Verification Scope: <Verbatim from Section 1>
   - [ ] UO-02: ...

   2. Technical Requirements to verify:
   - [ ] REQ-01 [UO-01]: <Verbatim EARS requirement from Section 2> -> Fulfills at [file:line](file:///...)
   - [ ] REQ-02 [UO-01]: <Verbatim EARS requirement from Section 2> -> Fulfills at [file:line](file:///...)

   Verification Rules:
   1. Use `view_file` ONLY. Do NOT run any terminal commands.
   2. Step 1 — Audit Requirements (Micro/Seam): For each REQ, start from the file cited at `-> Fulfills at [TargetSeam]`. Inspect signatures, type annotations, invariants, error handling, and any callers or consumers as needed to verify correctness.
   3. Step 2 — Audit User Outcomes (Macro/Wiring): For each UO, trace the full execution path from entry point to observable result as declared in its Verification Scope. Verify that the implementation is fully integrated into the runtime. If internal logic is correct (REQs pass) but the feature is not reachable or observable from the declared surface, mark the corresponding UO as FAIL.
   4. Output your evaluation in the following standardized dual-matrix format:

   ### Dual Verification Audit Report

   #### User Outcomes Audit
   | # | User Outcome | Subagent Status | Evidence |
   |---|---|---|---|
   | UO-01 | <Verbatim outcome> | PASS / FAIL | <Trace proof or failure reasoning with [file:line](file:///...) citations> |

   #### Technical Requirements Audit
   | # | EARS Requirement | Trace | Subagent Status | Seam Line Citations |
   |---|---|---|---|---|
   | REQ-01 | <Verbatim requirement> | UO-01 | PASS / FAIL | [file:line](file:///...) |

   #### Audit Verdict
   - Outcome Status: ALL PASS / HAS FAILURES
   - Requirement Status: ALL PASS / HAS FAILURES
   - Final Delivery Gate: PASS (100% across both) / FAIL
   ```
   ````

3. **Remediation Loop:**
   - If the subagent marks ANY requirement or user outcome as `FAIL`:
     - Formulate the approach to do it right.
     - Apply the fix in the code.
     - Re-spawn the verification subagent using the exact same verbatim prompt block.
     - Repeat until 100% of both outcomes and requirements are marked `PASS`.

### C. Completion Criteria (Mandatory Delivery Gate)
To finalize execution and declare completion, the executing agent MUST embed the real subagent dual audit tables (received from the live subagent response) directly inside `#### 2. Verification Proof` of its final `Execution & Verification Report`:

```markdown
#### 2. Verification Proof
- **Baseline Check:** `<Exact command(s) executed for verification>` -> `<Passing output summary line / exit code>`
- **Dual Subagent Audit Proof (Auditor ID: `<Conversation ID>`):**

  **User Outcomes Audit:**
  | # | User Outcome | Subagent Status | Evidence |
  |---|---|---|---|
  | UO-01 | `<Verbatim outcome>` | PASS | <Trace proof with [file:line](file:///...) citations> |

  **Technical Requirements Audit:**
  | # | EARS Requirement | Trace | Subagent Status | Seam Line Citations |
  |---|---|---|---|---|
  | REQ-01 | `<Verbatim requirement>` | UO-01 | PASS | [file:line](file:///...) |
```

Execution is strictly INCOMPLETE if any row in either the User Outcomes Audit or Technical Requirements Audit has status `FAIL` or is missing.
