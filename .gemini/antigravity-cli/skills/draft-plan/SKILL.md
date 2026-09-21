---
name: draft-plan
description: Draft plan after confirm approach
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved proposal into a **self-contained** `implementation_plan.md` Artifact.
The plan's sole purpose is **instant, zero-read execution**: once approved, coding must proceed immediately without inspecting any additional files for context. Enforce literal boundary interfaces paired with the **Closed Scope Invariant** ($\text{Unbound References} = \emptyset$) so every structure manipulated by the target logic is fully bound within the plan. Enforce independent subagent audit for verification.

---

## Context & Intent

Every plan begins with a concise natural-language overview establishing technical context before formal contracts (senior engineer direct tone, zero dumbing down):
- **Current System Context:** Where the affected components sit within the broader system today — runtime environment, architectural boundaries, and current data flow.
- **Problem & Purpose:** The specific gap, failure mode, or requirement this change addresses and why it exists.
- **Proposed Mechanism:** Operational flow of the change — what actual components and mechanisms will do to solve the problem.
- **Crucial Nuances:** Key architectural constraints, trade-offs, or non-obvious realities highlighted explicitly.

*Rules:* Name actual components and mechanisms; short, precise sentences without conversational filler; establish the mental model before presenting contracts.

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

## 2. Requirements & Seam Tracing

Translate approved requirements into checkable behavioral statements with bidirectional tracing:

- [ ] **REQ-01 [UO-01]:** When <Trigger>, <system/component> shall <Action>. -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-02 [UO-01]:** If <Condition/Error>, <system/component> shall <Action>. -> Fulfills at [TargetSeam](file:///path#L10)
- [ ] **REQ-03 [UO-02]:** <system/component> shall <Action>. -> Fulfills at [TargetSeam](file:///path#L10)

**Bidirectional Tracing Rules:**
- Every `UO-xx` must be served by at least one `REQ-yy`; every `REQ-yy` must cite its fulfilling seam link (zero orphan requirements or outcomes).
- Multi-stage pipelines annotate entry ingress and terminal sink: -> Ingress: [entry](file:///path#L10) | Egress: [sink](file:///path#L80).

---

## 3. Affected Files

### Scope & Semantic Context Discovery
1. **Mutation Scope (Files to mutate):** Starting from each UO's Verification Scope and each REQ's Fulfills-at target, trace callers and consumers outward using `grep_search` and `view_file`. At each hop, determine whether the file requires changes to fulfill the plan. If yes, add it to the manifest and trace its callers/consumers in turn.
   - **Fixed-point criterion:** Scope discovery is complete when an additional trace hop produces no new files requiring changes.
2. **Semantic Scope Closure (References to bind):** For every seam identified, enforce the **Closed Scope Invariant**: every reference required to author the target logic must be structurally bound within the plan. Trace upstream definitions until the set of unbound references is empty:
   $$\text{Unbound References} = \emptyset$$
   Read-only files containing referenced structures are not added to the Mutation Manifest, but their resolved definitions are inlined into the plan's seam context.

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

## 4. Design Definition (`Literal Boundary Contracts & Closed Scope`)

For every target file to create (`[NEW]`), modify (`[MODIFY]`), or delete (`[DELETE]`), pinpoint exact line ranges using clickable [basename](file:///path#L10-L20) links without backticks and declare literal physical contracts:

- **Target Seam, Signatures & Bound Structures:**
  - Define external boundaries: `class` / `def` signatures with complete type annotations, docstrings, and `...` (ellipses) method bodies.
  - **Closed Scope Context:** For every reference crossing or evaluated within the seam boundary, declare its concrete structural shape (the exact accessible properties, methods, or variants utilized by the implementation). An execution agent must possess complete structural knowledge without querying external definitions.
- **Causal Execution & State Transitions:**
  - If execution involves multiple state transitions or external side effects, declare their strict causal order between entry preconditions and exit invariants. If single-step or pure computation, omit entirely — never fabricate artificial stages.
- **Exact Caller & Downstream Sink Audit (`grep_search & dataflow proof`):**
  - **Caller Audit (Ingress):** Run `grep_search` across workspace for this symbol. List every caller [file:line] requiring update, or state: "Caller Audit: 0 production callers found via grep_search."
  - **Sink Audit (Dataflow):** Trace return values, mutations, or emitted events downstream to their **Terminal Sink** (HTTP response, persistent store, external queue, or UI render), or state: `"Sink Audit: Terminal sink reached at this seam."`
  - **Composition Wiring:** Specify exact instantiation or mounting points in the application lifecycle (DI container, route table, CLI registry).
- **Invariants & Hermeticity:**
  - Declare boundary invariants (what must remain true across execution), explicit error modes (typed exceptions / return variants), and any out-of-band state accessed outside parameter injection (environment, disk, undeclared globals).

---

## 5. Verification & Validation Proof

In `implementation_plan.md`, define the mechanical, checkable verification steps to be executed:

### A. Baseline Check
- Specify exact terminal commands (`e.g.,` typecheck, lints, builds, smoke tests) executing against the target interfaces.

### B. Independent Subagent Dual Audit Directive
Copy the directive below verbatim into `implementation_plan.md`.
**Single Variable Rule**: The ONLY dynamic value is replacing `<plan-link>` with the clickable link `[implementation_plan.md](file:///...)` to the current plan.

````markdown
#### Subagent Spawn Directive (Post-Implementation)
> [!IMPORTANT]
> After completing all code implementation, spawn the standalone `plan-auditor` subagent via `invoke_subagent`:
> - **TypeName**: `plan-auditor`
> - **Role**: `Plan Auditor`
> - **Prompt**: `Audit implementation plan at <plan-link>. Execute your dual verification protocol and deliver audit_report.md to the directory containing <plan-link>.`
````


### C. Convergence & Circuit Breaker Protocol
Declare execution bounds directly in `implementation_plan.md`:
- **Audit Budget**: Maximum 2 verification cycles. If verification fails on the second attempt, trigger an immediate **Hard Stop**.
- **Failure Dichotomy**: On Hard Stop, determine contract satisfiability before escalating:
  - **Design Flaw**: The contract is unsatisfiable under system reality.
  - **Reasoning Flaw**: The contract is satisfiable, but the implementation approach fails to converge.

---

## 6. Plan Completion Criterion (`Closed Scope Gate`)

Before finalizing `implementation_plan.md`, audit against the **Closed Scope Invariant**:
- Can an execution agent implement the target logic end-to-end without running a single investigative search or read tool (`grep_search`, `view_file`)?
- Does any seam rely on an unbound reference whose structural properties must be discovered at execution time?

If any reference remains unbound, the plan is INCOMPLETE: trace the upstream definition, bind its structure into the plan, and re-audit until:

$$\text{Unbound References} = \emptyset$$
