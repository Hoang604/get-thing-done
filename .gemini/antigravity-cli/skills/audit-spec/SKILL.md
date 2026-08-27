---
name: audit-spec
description: Adversarially audit SPEC.md across structural integrity and universal system completeness lenses, interactively repairing entropy
disable-model-invocation: true
---

# CORE DIRECTIVE

Adversarially audit `./.gtd/<task_name>/SPEC.md` for both **Structural Integrity** (internal logic defects) and **System Completeness** (omitted real-world boundaries). Instead of passively reporting defects, interactively resolve every gap with the user using decision-framed choices and pre-calculated recommended defaults, then patch `SPEC.md` in-place using strict EARS syntax with zero engineering leakage.

---

# PRIMARY TIER: ORDERED STEPS (`Immediate Action`)

## Step 1: Two-Tier Adversarial Entropy Scan

Read `./.gtd/<task_name>/SPEC.md` on disk. Systematically audit the specification across two complementary tiers:

### Tier 1: Structural Integrity (`The Syntactic Scan`)
Hunt for logical and grammatical defects in the text already written:
1. **Dangling States (`Dead Ends`):** Verify every `When`, `While`, or `If` clause references explicitly defined upstream entities/inputs and leads to a defined downstream exit state. Flag unlinked triggers or dead-end states.
2. **Missing Fallbacks (`Unhandled Errors`):** For every event/operation where failure is logically or physically possible, verify an explicit EARS `Unwanted` fallback (`If X fails, then Y`) is defined.
3. **Contradictions (`Invariant Collisions`):** Cross-reference all rules against stated Product/System Invariants and Core Goals. Flag mutually exclusive requirements.
4. **Unobservable Vagueness (`Verification Gaps`):** Flag subjective terms (`"fast"`, `"efficient"`, `"sometimes"`, `"clean"`, undefined thresholds) that cannot be machine-verified without human interpretation.

### Tier 2: System Completeness (`Universal Lens Projection`)
Project the specification against the **5 Universal Lenses**, auditing only dimensions physically touched by the system's operational surface:
1. **Resource & State Lifecycle:** Resource allocation, state mutation, and teardown/cleanup on normal exit or sudden interruption (SIGINT, crash, exception).
2. **Input & Scale Extremes:** Behavior at boundary extremes (0-byte / empty / null inputs, unbounded scale, malformed schemas, buffer limits).
3. **Execution Context & Preconditions:** Caller privileges, file/resource permissions (`EACCES`), environment preconditions, platform/OS compatibility, and prerequisite dependencies.
4. **Causality, Partial Failure & Interruption:** Multi-step mutation atomicity, rollback or temp-file cleanup on partial failure, and explicit error channels.
5. **Concurrency, Contention & Re-entrancy:** Behavior under simultaneous execution, shared resource contention, lockfiles, race conditions, and safe re-execution (idempotency).

*Confidence Horizon:* If the task is exploratory (spike/prototype), close unconstrained Tier 2 dimensions as provisional assumptions without halting for resolutions.

### Zero Entropy Exit
If zero entropy points are found across both tiers, output:
`**[ENTROPY: ZERO]** — Specification is structurally airtight and system-complete.`
Halt immediately.

---

## Step 2: Interactive Resolution Gate (`Interview Discipline`)

When entropy points are discovered, switch state header to `[CONSULT-interview]`.

Do NOT dump raw defect lists. Convert every discovered gap into a structured `ask_question` round (batching $\le 4$ related questions per turn):

- **Question Formulation:** Clearly state the omitted scenario, boundary gap, or failure mode.
- **Pre-calculated Defaults:** For every question, formulate a concrete, domain-sound fallback based on best practices and list it first marked as `(Recommended)`.
- **Decision-Framed Options:** Present 2–3 mutually exclusive options formatted as:
  `<Concrete System Fallback> — Choose this if <operational trade-off>`
- **Option Array Contract:**
  - Option 1: `(Recommended) <Concrete fallback> — <rationale>`
  - Option 2: `<Alternative fallback> — <rationale>`
- `is_multi_select: false`.

---

## Step 3: In-Place EARS Patching (`Spec Discipline`)

Once the user selects or approves an option:

1. **Direct Disk Mutation:** Immediately append or update the relevant section of `./.gtd/<task_name>/SPEC.md` using `replace_file_content` or `write_to_file`.
2. **EARS Syntax Enforcement:** Format all patched requirements strictly in EARS syntax:
   - **Unwanted Event (Fallbacks):** `If <unhandled failure/boundary condition>, then the <System> shall <explicit recovery/exit behavior>.`
   - **Event-Driven:** `When <trigger/input>, the <System> shall <system response>.`
   - **State-Driven:** `While <state/mode>, the <System> shall <system response>.`
3. **Zero Engineering Leakage Guard:** Restrict vocabulary strictly to system entities/inputs, observable triggers, error exit codes, payloads, and UI/CLI output states. Strictly forbid class names, function signatures, or code topology.
4. **Atomic Invariant Reconciliation:** If a contradiction was resolved, replace conflicting text atomically to ensure 100% internal consistency.

---

## Step 4: Verification & Hand-off

Re-scan `./.gtd/<task_name>/SPEC.md` across both tiers until all entropy points are resolved (`[ENTROPY: ZERO]`).

Output the exact hand-off message and halt:

```text
**[SPEC AUDITED & LOCKED]** — All system fallbacks, invariants, and edge cases sealed in ./.gtd/<task_name>/SPEC.md.

Next Steps:
- To decompose into dependency-ordered tracer-bullet tickets: run `/to-ticket`
- To begin technical architecture and trade-off analysis: run `/propose-plan`
```

Stop execution immediately. Do NOT write an implementation plan or mutate source code.

---

## Postfixes
- `-audit`: Scanning `SPEC.md` across structural and system tiers.
- `-interview`: Prompting user via `ask_question` with recommended fallbacks.
