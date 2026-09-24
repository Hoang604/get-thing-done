---
name: refactor-plan
description: Plan an architectural refactor or breaking capability using dual invariance, verification realignment, and dynamic burndown
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved refactor or breaking capability approach into a self-contained `implementation_plan.md` Artifact.
Execution steers thought through **Dual Invariance** (Intent and Structure) and action through **Topological Burndown**. Output the artifact, then halt execution.

---

## 1. Dual Invariance (Intent & Structure)

Every refactor plan balances functional capability with structural integrity:

- **Intent Invariance (Doing the Right Thing)**: The goal establishes the essential invariant rule(s) governing the target capability, from which the execution agent deduces every downstream adaptation without requiring per-file checklists. It is verified exclusively by an observable acceptance signal at the terminal boundary.
- **Structural Invariance (Doing Things Right)**: State flows strictly along the dependency DAG. Upstream contracts must be sealed before downstream targets are mutated. Downstream compilation errors are expected intermediate states until reached; injecting fake optionality (`?`) or fallbacks (`??`, `||`) violates structural invariance.
- **Verification Realignment**: Existing test suites assert obsolete contracts and will fail. Tests are downstream consumers: fixtures and assertions must be updated to reflect the new invariant. Modifying production code with surrogate fallbacks or dummy defaults to appease failing verification is strictly forbidden.
- **Dual Convergence**: Execution terminates if and only if both invariants hold:
  $$\text{Diagnostic Error Count} == 0 \quad \land \quad \text{Acceptance Signal Verified}$$

---

## 2. Dynamic Burndown Frontier

Do not pre-enumerate affected dependents. The compiler or typechecker is the authoritative oracle of the active frontier:
$$\text{Frontier} = \{ f \in \text{Codebase} \mid f \text{ violates the updated upstream contract} \}$$

Dependent migration executes as a fixed-point burndown: resolve caller lineage iteratively to satisfy the Intent Invariant until the diagnostic set converges to empty ($\text{Diagnostics} = \emptyset$).

---

## 3. Plan Artifact Contract (`implementation_plan.md`)

Write the plan to `<appDataDir>/brain/<conversation-id>/implementation_plan.md` using `write_to_file`.
The plan must be a concrete, closed-scope contract adapted to the target domain, structured strictly as follows:

```markdown
# Implementation Plan: <Refactor or Capability Name>

## 1. Invariant Contract Anchor
- **Root Boundary**: [<file>](file:///path) (Authoritative source where contracts originate)
- **Generative Invariant(s)**: The non-negotiable rule(s) enforced at the boundary. Zero optionality or legacy retention.
- **Root Verification Gate**: Isolated command verifying the root contract (downstream caller errors are expected).
- **Terminal Acceptance Signal**: Concrete command verifying the active capability at the terminal boundary.

## 2. Topological Lineage Sequence
An ordered list of specific targets to mutate along the dependency DAG from root to terminal boundary:
1. [<upstream_target>](file:///path): Consumed invariants, emitted guarantees, and mutation scope.
2. [<intermediate_target>](file:///path): State propagation without local fallback injection.
3. [<terminal_target>](file:///path): Wires state to fulfill the Terminal Acceptance Signal.

## 3. Verification Realignment
- **Obsolete Assertion Audit**: Specific test suites or verification fixtures that assert the legacy contract and will fail.
- **Realignment Mandate**: Direct requirement to update or delete obsolete assertions to match the new invariant. Modifying production code with surrogate fallbacks or dummy defaults to appease failing verification is strictly forbidden.

## 4. Dual Convergence Proof
- **Structural Diagnostic**: Workspace-wide diagnostic command terminating at `Error Count == 0`.
- **Behavioral Proof**: Terminal acceptance signal passing 100% green.
```

Output the link to `implementation_plan.md` and wait for user's next request.
