---
name: purge-fallbacks
description: Scan, classify, and eliminate defensive fallback operators and state fabrication in favor of Fail-Fast Invariant Assertions across the codebase.
disable-model-invocation: true
---

# Purge Fallbacks & Invariant Restoration

## 1. Generative Principle: The Boundary Membrane

A software boundary is a **validation membrane**, never a **state fabricator**.

Every boundary transition (network ingress, deserialization, DOM measurement, runtime capability negotiation) evaluates to exactly one outcome:
1. **Admit**: Pass the valid, complete domain state through untouched.
2. **Reject**: Fail-fast immediately (`throw InvariantViolationError`) when structural invariants are violated, or yield an explicit unsettled signal when layout has not converged.

### The Fabrication Anti-Pattern
Any inline operator (`??`, `||`, `?: dummy`) or sanitization branch that synthesizes unmeasured coordinates, replaces a local container with global dimensions, or demotes a corrupted entity into an empty default is **State Fabrication**. Downstream consumers must never receive fabricated state.

---

## 2. Invariant Classification Grammar

Evaluate every detected fallback against the binary membrane contract:

| State Class | Observable Property | Required Action |
|---|---|---|
| **Invariant** | Load-bearing identity, spatial coordinate, geometry dimension, or structural relationship. | **Eliminate fallback**. Require non-optional type upstream and assert fail-fast at boundary. |
| **Unsettled Lifecycle** | Transient measurement during mount, resize, or asynchronous layout convergence. | **Eliminate surrogate defaults**. Skip frame execution or suspend computation until layout settles. |
| **Legitimate Optional** | Explicitly declared optional field in API schema with authoritative empty semantics. | Preserve contract-declared default constant. |

---

## 3. Execution Protocol

### Step 1: Discover Candidates
Run the scanner across the target scope:
```bash
bash .agents/skills/purge-fallbacks/scripts/scan-fallbacks.sh [optional-path]
```
*Completion Criterion*: Scanner produces candidate list across the target scope.

### Step 2: Binary Membrane Audit
Classify every candidate line:
- If the fallback fabricates state for an **Invariant** or an **Unsettled Lifecycle**, mark as **Fabrication Violation**.
- If the candidate is a boolean condition (`if (a || b)`), bitwise codec, or discriminated union type guard, mark as **Scanner Noise**.
*Completion Criterion*: Zero unclassified candidate lines remaining.

### Step 3: Eliminate Fabrication
1. Replace all invariant fallbacks with explicit `InvariantViolationError` throws.
2. Replace all surrogate dimension fallbacks with unsettled lifecycle guards (early return/skip frame).
3. Correct upstream TypeScript contracts from `prop?: Type` to `prop: Type`.
*Completion Criterion*: Target scope contains zero fallback operators on invariant fields.

### Step 4: Verification Gate
Execute workspace validation:
```bash
npm run validate
```
*Completion Criterion*: 0 test failures, 0 lint errors, 0 typecheck errors.
