---
name: create-test
description: Propose a boundary test plan that passes all four REAL test rules and implement it after user approval.
disable-model-invocation: true
---

Every test you propose and write must earn a **REAL** verdict under all four rules:

1. **Contract.** The test guards a rule that the code under test promises to whoever calls it or reads its output, and the rule holds for every valid input. State that promise in one sentence that quotes none of the test's literal values and leaves no room for an output that satisfies the sentence while breaking what a caller of that behavior relies on. If the only sentence you can write repeats the test's expected value, the test pins an outcome, not a contract.

2. **Kills a mutant.** Name a plausible edit to one product line (`file:line`, old → new) that breaks the rule in 1, where product logic carries the change to an assertion and turns it red, and that no other REAL test in scope already kills just as directly. Every part of the outcome that the rule in 1 determines for this test's input must be checked by an assertion, so that no plausible edit to a product line can violate the rule in 1 on this input and still leave the test green (a **surviving mutant**). If the values being compared travel from the test's setup to its assertion without passing through any product decision, no product mutant can reach that assertion.

3. **Survives refactors.** Every edit that keeps the contract leaves the test green. Each assertion may observe only what the contract promises. Anything else it observes is something a refactor is allowed to change.

4. **Reaches the product.** The test enters the product the same way its real callers do, starts from state the real path can produce, and gets the same outcome on every run in the tier where it is filed. Stand-ins are used only at out-of-process boundaries that cannot run locally in the test tier, and each stand-in implements the boundary's stateful contract rather than recording calls.

## Steps

1. **Trace.** Read the product code in `<scope>`, its callers, and every existing test covering `<scope>`. Identify each contract rule in `<scope>` whose plausible product mutants are not yet killed by an existing REAL test. When a behavior in `<scope>` has no source or user ruling establishing whether it is promised to callers, ask the user before proposing a test for it.
   *Done when* every unguarded contract rule in `<scope>` has all five of these filled in with concrete content:
   - the contract sentence
   - the mutant killed as `file:line` old → new
   - the surviving mutant check (`none`)
   - the refactor that turns it red (`none`)
   - the reach path and test runner command

2. **Propose.** Write `<appDataDir>/brain/<conversation-id>/test-plan.md` with `ArtifactMetadata` (`UserFacing: true`, `RequestFeedback: true`, `Summary: ...`) containing the workspace test runner command and the planned tests formatted to the anchor below, then stop and wait for user approval.
   *Done when* `<appDataDir>/brain/<conversation-id>/test-plan.md` is written to the anchor below with `Surviving mutant` and `Refactor that turns it red` both equal to `none` on every row, and the turn ends awaiting the user's approval.

```markdown
Test command: `pytest tests/unit/test_account.py`

| Test | Contract | Mutant killed | Surviving mutant | Refactor that turns it red | Reach |
|---|---|---|---|---|---|
| `tests/unit/test_account.py::test_withdraw_rejects_overdraft` | Withdrawing more than the balance raises Overdraft and leaves the balance unchanged | `account.py:42` `if amount > self.balance:` → `if False:` | none | none | public `withdraw()`, assertions on `Overdraft` and `account.balance` |
```

3. **Implement and verify.** After the user approves `test-plan.md`, write the approved tests into the target test files. Run the tests in `<scope>` twice with the workspace test runner. For each newly written test, apply its declared `Mutant killed` edit (`file:line`, old → new) to the product file, run the test to witness it turn **red**, and restore the product file. Run the tests in `<scope>` one final time to confirm a clean pass.
   *Done when* every approved test passes two consecutive runs with the same outcome, turns red when its `Mutant killed` edit is applied to the product code, and passes again after the product code is restored.
