---
name: create-test
description: Propose boundary test plan as an interactive artifact and implement upon user approval
disable-model-invocation: true
---

# GENERATIVE PRINCIPLES (Thought Direction)

- **The Seam is the Test Surface:** An interface is the entire observable boundary of a module: its public signature, observable state transitions, and typed failure contracts. Testing must cross this exact consumer boundary. Any assertion relying on private methods, unexported state, or intermediate call counts couples tests to implementation details and is strictly invalid. Refactorings that preserve caller-observable behavior must never break tests.
- **Fidelity Maximization:** Tests must execute against the highest-fidelity runtime machinery available. Real in-process execution takes precedence over all else. Stand-ins are authorized strictly at unmanaged physical boundaries (network I/O, external systems) and must implement stateful domain contracts (in-memory fakes) rather than call-recording stubs.
- **Mutation & Observable Oracles:** A test exists solely to expose regression. Every test case must declare a concrete `Breaks-If` mutation: the plausible bug or inverted invariant that causes the test to fail red. Assertions must verify the contract directly (state post-conditions or typed rejections); assertions that pass despite corrupted business logic are tautologies.
- **Hermetic Isolation & Diagnostic Quality:** Tests must be completely self-contained, order-independent, and leak zero state. Assertions must compare explicit domain values to produce pinpoint diffs upon failure, avoiding aggregated boolean checks.

---

## Step 1: Propose Test Plan (Artifact Gate)

Investigate the target seam to ground its observable behavior and workspace test harness in verified source code. Generate the test plan artifact at `<appDataDir>/brain/<conversation-id>/test-plan.md` using `write_to_file` with `ArtifactMetadata` (`UserFacing: true`, `RequestFeedback: true`, `Summary: ...`).

The artifact captures verified source baselines (`CODE [file:line]`), flags unconfirmed claims (`⚠️ ASSUMPTION — needs human confirmation`), defines the workspace test command, and centers on the **Adversarial Test Matrix**:

| Target Seam | Invariant Under Test (`Observable Contract`) | Stand-in Mechanism | Breaks-If Mutation (`Specific Bug Caught`) | Real-World Impact (Pass Guarantee vs Fail Consequence) |
| :--- | :--- | :--- | :--- | :--- |
| `[seam_signature]` | Expected state transition or typed rejection | Real execution, local fixture, or contract fake | Plausible bug that turns test red | Pass: Plain-language system guarantee \| Fail: Unwanted situation direct user encounters |

**Completion Criterion:** Wait for user approval.

---

## Step 2: Implement & Mechanically Prove

*Precondition: Run strictly after the user explicitly approves the Step 1 artifact.*

Translate the approved test matrix into hermetic test code matching the codebase harness, tagging unverified assumptions with `# ⚠️ UNVERIFIED ORACLE`. Prove the implementation mechanically:
1. Execute the workspace test runner to verify a green pass.
2. Conduct a mutation proof on pre-existing code by deliberately corrupting the invariant under test to witness a red failure, then restoring it to green.

**Completion Criterion:** The test suite passes cleanly, and mutation sensitivity (failing red under fault injection) is verified.
