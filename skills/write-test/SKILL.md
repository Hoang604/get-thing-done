---
name: write-test
description: manual trigger by user, do not auto invoke
---
<philosophies>

## 1. Engineering Bedrock (Logic vs Boundary)

- **Unit Tests (The Logic Firewall):** Focus on Pure Logic, State Transitions, and Edge Cases. _Mock all I/O._
- **Integration Tests (The Boundary Guard):** Focus on the _wiring_ between components and real I/O (Database, API).
- **Abstraction:** Tests must verify the _Contract_ (Public API), never the _Implementation_ (Internals).

## 2. The Invariant Principle & Property-Based Testing

Do not just test "Inputs -> Outputs" via Example-Based Unit Tests. Test **State Consistency**:

- _Pre-conditions:_ What _must_ be true before?
- _Post-conditions:_ What guaranteed state exists after?
- _Mathematical Verification:_ Propose Property-Based Testing for critical logic to generate adversarial, randomized inputs across the entire state space to verify physical limits and zero-trust boundaries.

## 3. Adversarial Design (The "Breaker" Mindset)

Assume the implementation will be naive. Design tests that punish laziness and test for physical friction limits:

- **Attack Vectors:** `Null`, `Empty`, `Max Int`, `Unicode`, `Injection`.
- **State Conflict:** What if this is called twice rapidly? (Test for Race Conditions).
- **Dependency Failure:** What if the DB times out? (Test Circuit Breakers).
- **Resource Exhaustion:** Test for unbounded queue limits or lack of backpressure.
- **Zero Assumption:** Never assume a function works. Prove it.

</philosophies>

<process>

## 1. Contextual Analysis

1.  **Ingest** `PLAN.md` to identify the _Scope of Work_ (Tasks 2, 3, etc.).
2.  **Ingest** `SPEC.md` to map _Requirements_ to _Assertions_.
3.  **Identify Dependencies:** Distinguish between _Pure Logic_ (Unit Testable) and _I/O Boundaries_ (Integration Testable).

## 2. Strategy Formulation

Construct a TDD plan that enforces the architecture:

- **Unit Suites:** Logic branches, state integrity, invariant protection, property-based tests.
- **Integration Suites:** Component wiring, real DB access, API contracts.
- **Failure Modes:** Explicit error handling (timeouts, circuit breakers, capacity rejection).

## 3. The Injection (Execution)

Using the `replace_file_content` tool, locate the `<task>` block containing `<!-- TDD_STRATEGY_SLOT -->` and overwrite the **ENTIRE** task block with your specific strategy.

**Drafting the Task Content:**
The new Task 1 must be concrete. Use this structure:

```xml
<task id="1" type="auto" complexity="Low/Medium/High">
  <name>TDD Strategy: {Phase Name}</name>
  <risk>Prevents architectural drift and regression.</risk>
  <files>
    {List specific test files to be created}
  </files>
  <action>
    Implement the following test suites. Ensure tests FAIL (Red) before implementation begins.

    ### 1. Unit: The Logic Firewall ({Component Name})
    *Focus: Pure Logic, Invariants & State Transitions. Mock all I/O.*
    - [ ] **Test: {Feature} - Happy Path**
      - *Context:* {State setup}
      - *Input:* {Valid input}
      - *Assertion:* Returns {Result} AND State is {New State}.
    - [ ] **Test: {Feature} - Boundary Attack**
      - *Input:* {Null/Empty/Max/Invalid}
      - *Assertion:* Handles gracefully (throws {Specific Error} or returns Default).
    - [ ] **Test: {Feature} - Invariant Protection (Property-Based)**
      - *Input:* {Adversarial Randomized State Space}
      - *Assertion:* System refuses transition, remains in {Safe State}.

    ### 2. Integration: The Boundary Guard ({Boundary Name})
    *Focus: I/O Wiring & Component Contracts.*
    - [ ] **Test: {Scenario}**
      - *Scope:* Real DB, Mocked External API.
      - *Flow:* {Component A} calls {Component B}.
      - *Assertion:* Data is persisted correctly to DB.

    ### 3. Resilience & Errors (Friction limits)
    - [ ] **Test: Failure Recovery & Circuit Breaking**
      - *Condition:* Dependency throws Critical Error (Timeout/500).
      - *Assertion:* System degrades gracefully (does not crash).
    - [ ] **Test: Backpressure / Capacity Limits**
      - *Condition:* Flood with requests beyond capacity limit.
      - *Assertion:* System returns 429 Too Many Requests (or similar), memory does not exhaust.
  </action>
  <done>
    - Test files created with imports/scaffolding.
    - `npm test` runs and reports specific failures (Red State).
  </done>
</task>
```

</process>

<prohibitions>

- **Do NOT** write the actual test code (JS/Python). Write the _specification_.
- **Do NOT** modify Tasks 2, 3, etc. Only upgrade Task 1.
- **Do NOT** remove the XML structure of the task.
- **Do NOT** output the plan to chat. You must edit the file directly using `replace`.
- **Do NOT** propose next steps, future actions, or user instructions in the final result. Output only the work done.

</prohibitions>
