---
name: spec
description: Define domain requirements and edge cases in EARS syntax without code leakage
disable-model-invocation: true
---

# CORE DIRECTIVE

Convert a feature request into a zero-entropy, reviewable `SPEC.md` specification file by interviewing the user relentlessly and progressively building the document on disk. Never merge unverified assumptions into the specification.

---

# PRIMARY TIER: ORDERED STEPS (`Immediate Action`)

## Phase 1: Interview & Progressive Specification (`Relentless Interview`)

You are authorized and recommended to **interview the user relentlessly** until domain ambiguity (`domain entropy`) reaches zero. Build `./.gtd/<task_name>/SPEC.md` progressively as information blocks are confirmed.

### 1. Batched Interview & Recommended Defaults
- **Batched Delivery:** Ask <= 5 clarifying questions per turn. For every confirmed requirement, dynamically trace and interrogate its immediate prerequisites (`upstream dependencies`) and unstated boundary fallbacks (`downstream failure states`) across turns. Walk down every branch of the decision tree to eliminate implementation ambiguity (`multiple conflicting valid behaviors or missing error fallbacks`). Do not stop until a downstream developer could implement every domain rule without inventing or assuming a single missing rule.
- **Mandatory Defaults:** For every question asked, explicitly provide a concrete, recommended default fallback based on domain best practices.
- **Auto-Locking:** If the user approves the recommended defaults or commands drafting (`e.g., "proceed", "looks good"`), lock all unanswered edge cases to their recommended defaults.

### 2. Progressive BA/RA File Building
- Do not wait until the end of the interview to write `SPEC.md`.
- **Incremental Updates:** Every time the user confirms an information block (`e.g., Scope & Reality, specific domain rules, error handling`), immediately write or append those verified sections to `./.gtd/<task_name>/SPEC.md` using `EARS Syntax` (consult `Reference Tier` below).
- By the end of Phase 1, `./.gtd/<task_name>/SPEC.md` must be a single, comprehensive specification document containing all confirmed requirements and invariants (`domain entropy = 0`).

### 3. Continuous Contradiction Audit (`Reconcile Engine`)
- **Cross-Reference Audit:** Before writing any new answer to `SPEC.md`, cross-reference it against confirmed **Product Invariants**, existing **EARS Requirements**, and the core **Business Goal**.
- **Stop & Reconcile:** If the user's answer contradicts a prior confirmation or introduces unmotivated on-the-fly scope creep, **do NOT append it to `SPEC.md`**. Output an explicit **`[RECONCILE]`** block:
  1. **The Collision:** State exactly which requirement or invariant is contradicted.
  2. **The Trade-off:** Explain why both cannot coexist in the domain logic.
  3. **The Forced Choice:** Present exact options (`Option A: Supersede prior rule with new requirement` vs `Option B: Reject new requirement and keep prior rule`) alongside a **Recommended Resolution**.
- **Atomic Update:** Once the user selects an option, immediately update `./.gtd/<task_name>/SPEC.md` so the specification maintains 100% internal consistency (`zero contradiction entropy`) at all times.

---

## Phase 2: Execution Roadmap (Adaptive Branching & Slicing)

Once all domain branches are confirmed (`domain entropy = 0`) and written to `./.gtd/<task_name>/SPEC.md`, evaluate the domain scope to select the execution branch:

### Step 1: Branch Selection (`Complexity Gate`)
- **Branch A (`Single-Slice Feature` — Direct Completion):** If all confirmed EARS requirements and error fallbacks can be delivered and `Black-Box Verified` within **a single end-to-end domain deliverable** (`e.g., a single synchronous user flow, an atomic API transaction, or a localized UI component`), **DO NOT append an Execution Roadmap**. Proceed directly to `Step 3: Completion Contract`.
- **Branch B (`Multi-Slice Epic` — Domain Roadmap):** If the confirmed requirements span **multiple decoupled domain milestones, independent user personas/portals, or asynchronous temporal stages** that must be delivered and verified sequentially (`e.g., Phase 1: Ingestion Engine -> Phase 2: Rating & Billing -> Phase 3: Dunning & Retry`), append a sequential execution roadmap to `./.gtd/<task_name>/SPEC.md` (`Step 2`).

### Step 2: Append Roadmap (`Branch B Only`)
Conclude `./.gtd/<task_name>/SPEC.md` with a sequential phase breakdown to prevent context-window overload and state explosion during downstream implementation:

- **Strict Domain Scope Guardrail:** Output strictly **observable domain deliverables and acceptance criteria** (`WHAT/WHY`). Enforce `Reference B` (`Zero Engineering Leakage`). Never list file paths, code topology, or architectural seams (`WHERE/HOW`).
- **Vertical Slicing (`Tracer Bullet Contract`):** Each phase MUST cut a narrow but COMPLETE vertical slice through the domain logic. A phase must deliver an independently demonstrable or `Black-Box Verifiable` user/system value (`e.g., Phase 1: Ingestion to DB -> Phase 2: Billing Calculation -> Phase 3: Dunning Retry`). Strictly prohibit horizontal layer-by-layer phases (`e.g., forbidden: Phase 1 only DB schemas, Phase 2 only APIs`).
- **PR Scope Sizing (`Internal Legwork`):** Estimate complexity internally. Size each vertical slice phase to approximately **1 PR scope** (`<= 5 core seams/files when implemented`), recording strictly observable domain boundaries in `SPEC.md`.

### Step 3: Completion Contract
- **Interactive Execution (`Default`):** Output exactly `Please review ./.gtd/<task_name>/SPEC.md. I will await your explicit confirmation or next instruction.` and stop calling tools.

---

# SECONDARY TIER: IN-SKILL REFERENCE (`Consulted On Demand`)

## Reference A: File Persistence & Task Naming
- **Task Naming (`<task_name>`):** Invent a concise, kebab-case task name derived from the user request (`e.g., billing-dunning`). Must be **<= 3 words**.
- **No Artifacts:** Do NOT create an Artifact. Write directly to `./.gtd/<task_name>/SPEC.md` using `write_to_file` / `replace_file_content`.

---

## Reference B: Zero Engineering Leakage (`Strict Negative Guardrail`)

`SPEC.md` must capture strictly **WHAT** and **WHY**, never **HOW**.

- **Forbidden Vocabulary:** Never write file paths (`e.g., service.py`), function names (`e.g., process_order()`), class names, programming patterns, or database/table schemas.
- **Allowed Vocabulary:** Domain entities (`e.g., User, Order, Invoice`), observable system triggers, HTTP/gRPC status codes, JSON payloads, and user-facing UI states.
- **Infrastructure Contract Exception:** For pure infrastructure/technical features (`e.g., caching, distributed locking, event buses`), architectural contracts (`pub/sub topic, Redis TTL, LRU eviction`) are permitted. All requirements must remain strictly phrased as **observable state transitions and SLA contracts** without leaking internal code topology.

---

## Reference C: Requirements (`EARS Syntax & Mandatory Error Mapping`)

Every product requirement in `SPEC.md` must strictly follow EARS phrasing. Every trigger where failure is possible must define an `Unwanted` fallback:

- **Ubiquitous:** `The <System> shall <Domain Response>.`
- **Event:** `When <User/System Trigger>, the <System> shall <Domain Response>.`
- **State:** `While <System Mode / State>, the <System> shall <Domain Response>.`
- **Unwanted (`Mandatory Error Fallback`):** `If <Domain Error / Payment Failure / Timeout>, then the <System> shall <Exact Fallback Domain Response>.`
- **Optional:** `Where <Feature Flag / Tenant Option enabled>, the <System> shall <Domain Response>.`

All acceptance criteria must be **Black-Box Verifiable** (`observable from outside the system without reading code`).
