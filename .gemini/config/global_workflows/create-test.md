---
name: create-test
description: create test for required code
---

<role>
Design repo-specific test strategies and write test code.
- Investigate target code first.
- Declare oracle assumptions before proposing assertions.
- Design tests to catch real bugs, not mirror implementation.
- Present plan for approval.
- Write test code after confirmation.
</role>

<objective>
Create tests for target (module, feature, file, function, artifact).
Flow: Parse Target → Investigate Code → Detect Test Stack → Declare Oracle → Design Strategy → Mirror → Confirm → Execute
</objective>

<philosophy>
## 1. Investigate Before Designing
Inspect target code first. Read files, public contract, dependencies, match existing test patterns.
Only ask user for: priority behaviors, production edge cases, must-not-break.

## 2. Two-Layer Model
- **Unit Tests:** Test pure logic, state transitions in isolation. Mock I/O boundaries simply.
- **Integration Tests:** Test component wiring using real I/O.
- **Contract Rule:** Verify observable inputs/outputs, never internal implementation/private state.
- **Mock Drift Rule:** Prescribe integration test if mocks contain logical branching or state.

## 3. Invariants (No Tautologies)
Expected values must trace to:
1. Spec/business literal.
2. Verified human pre-computed constant.
3. Defining structural property.
Else flag: `⚠️ UNVERIFIED ORACLE — needs human confirmation`. Use property tests if logic has structural invariants.

## 4. Adversarial Design
- **Level 1 — Input:** Null, empty, boundary numbers, Unicode, bad formats.
- **Level 2 — Semantic:** Mocked OK with bad body, truncated write, balance going negative.
- **Level 3 — Conditional (if I/O/async):** Concurrency, capacity, timeout.

## 5. Metamorphic Testing
If absolute output unknowable (ranking/complex transform): verify relations (Invariance, Directional, Symmetry, Subset).

## 6. Causal Independence
Assert that changing independent variables must not change outcome.
</philosophy>

<process>

## 1. Parse the Target
Identify target from `{{args}}` (file, module, feature, function). Ask one question if ambiguous.

## 2. Investigate the Target Code
Read target code: API/contract, inputs/outputs, side effects, dependencies, business rules/invariants. Report findings before test design.

## 3. Detect Test Stack
Match repository framework, file naming (`*.test.ts`, etc.), directory structures, assertion style, mock style.

## 4. Declare Oracle
State ground-truth assumptions.
- **Behavioral:** Cite `CODE [file:line]`, `SPEC [doc §section]`, or `INFERRED`.
- **Boundary:** edges.
- **Causal Independence:** variables that must not affect outcome.
- **Unverified Assumptions:** `⚠️ ASSUMPTION` (user must confirm).

## 5. Design Test Strategy
Design concrete items:
```text
### Unit Tests — Logic & Invariants
- [ ] {What is tested} → VERIFY: {invariant / property / post-condition}
      SOURCE: {spec literal | pre-computed constant | structural property}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation that would cause this test to fail}

### Integration Tests — Boundary Contracts
- [ ] {Boundary scenario} → VERIFY: {contract holds}
      SOURCE: {spec | API doc | code contract}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}

### Semantic Adversarial Tests
- [ ] {Deceptive success scenario} → VERIFY: {detection / rejection}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}

### Edge Case & Error Tests
- [ ] {Failure scenario} → VERIFY: {error behavior}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}
```

## 6. Specify Test Files
List files to create/modify and items going in each.

## 7. Mirror the Plan
Present full plan. Show all items; do not collapse.

```text
---
  TEST PLAN — {target name}
---

Target: {what is being tested}
Test Framework: {detected framework}
Test Files: {files to create/modify}

Oracle Claims: {N} behavioral, {N} boundary, {N} independence, {N} unverified
Test Items: {N} unit, {N} integration, {N} adversarial, {N} edge case

---
ORACLE DECLARATION
---

### Behavioral Claims
- CLAIM: {what the system must do}
  SOURCE: {CODE [file:line] | SPEC [doc §section] | INFERRED — reasoning: ...}

### Boundary Claims
- CLAIM: {what the system must do at edges}
  SOURCE: {CODE [file:line] | INFERRED — reasoning: ...}

### Causal Independence Claims
- INDEPENDENT: {Variable X} must NOT affect {Outcome Y}
  SOURCE: {CODE [file:line] | INFERRED — reasoning: ...}

### Unverified Assumptions
- ⚠️ ASSUMPTION: {what you believe but cannot trace}

---
TEST STRATEGY
---

### Unit Tests — Logic & Invariants
- [ ] {What is tested} → VERIFY: {invariant / property / post-condition}
      SOURCE: {spec literal | pre-computed constant | structural property}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation that would cause this test to fail}

### Integration Tests — Boundary Contracts
- [ ] {Boundary scenario} → VERIFY: {contract holds}
      SOURCE: {spec | API doc | code contract}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}

### Semantic Adversarial Tests
- [ ] {Deceptive success scenario} → VERIFY: {detection / rejection}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}

### Edge Case & Error Tests
- [ ] {Failure scenario} → VERIFY: {error behavior}
      ORACLE REF: {which claim}
      BREAKS IF: {specific mutation}

---
```

**Wait for explicit approval. Do NOT write code before approval.**

## 8. Execute — Write Test Code
Write actual test files following stack conventions. Use descriptive names. Mark `⚠️ UNVERIFIED ORACLE` with comments.
Run test command to verify:
```bash
{detected test command} {test file path}
```

## 9. Final Report
```text
---
  TESTS WRITTEN ✓
---

Target: {what was tested}
Files created/modified:
  - {file 1}: {N} tests
  - {file 2}: {N} tests

Test run result: {pass/fail count}

---
```
</process>

<prohibitions>
- Do NOT design tests before investigating target.
- Do NOT write test code before user approval.
- Do NOT skip oracle declaration.
- Do NOT derive expected values from implementation logic.
- Do NOT force inapplicable test categories.
- Do NOT add boilerplate. Do NOT modify target code.
- Do NOT propose next steps after completion. Report results and stop.
</prohibitions>
