---
name: test-triage
description: Classify every test in scope as REAL or JUNK — REAL means it kills a plausible mutant of a consumer contract and survives every refactor that keeps the contract.
disable-model-invocation: true
---

A test earns its place by one property: it turns **red** exactly when someone relying on the product would see a break. This skill only classifies. The ledger is the whole deliverable, and every test file stays exactly as you found it.

## Verdict rule

A test is **REAL** when all four rules hold. It is **JUNK** when any rule fails.

1. **Contract.** The test guards a rule that the code under test promises to whoever calls it or reads its output, and the rule holds for every valid input. You can state it in one sentence that quotes none of the test's literal values. If the only sentence you can write repeats the test's expected value, the test pins an outcome, not a contract.

2. **Kills a mutant.** Name a plausible edit to one product line (`file:line`, old → new) that breaks the contract. Trace from that line: product logic has to carry the change to an assertion and turn it red. If the values being compared travel from the test's setup to its assertion without passing through any product decision, no product mutant can reach that assertion. The mutant also has to be one that no other REAL test in scope already kills just as directly.

3. **Survives refactors.** Every edit that keeps the contract leaves the test green. Each assertion may observe only what the contract promises. Anything else it observes is something a refactor is allowed to change.

4. **Reaches the product.** The test enters the product the same way its real callers do, starts from state the real path can produce, and gets the same outcome on every run in the tier where it is filed.

Boundary clips:
- An assertion that compares a value to a constant the test injected itself kills zero mutants, even when that value passes through product code that only copies it.
- An assertion on human-readable text breaks on refactors unless that exact text is itself the contract, such as a wire-protocol literal.

Classify each test as a whole. If even one assertion breaks rule 3 or rule 4, the test is JUNK, even when another assertion inside it would pass all four rules. Name that assertion in the evidence so the reader can see what is worth keeping.

## Steps

1. **Collect.** The scope is whatever paths the user names, or the whole suite if they name none. Collect all tests in `<scope>` using the workspace test runner and give every collected node ID its own ledger row.
   *Done when* the number of ledger rows equals the number of collected tests.

2. **Run twice.** Run the tests in `<scope>` two times using the workspace test runner and record each node's outcome from both runs. If a node's outcome differs between the runs, or if it errors, skips, or xfails for any reason other than a product defect its assertion catches, it fails rule 4.
   *Done when* every row has two recorded outcomes.

3. **Trace.** For each row, read the test body, its fixtures, and every product function between the test's call and its assertions. Then apply the four rules.
   *Done when* every row has all four of these filled in with concrete content:
   - the contract sentence, or the outcome the test pins
   - the mutant as `file:line` old → new, or the reason no mutant reaches an assertion
   - a contract-preserving edit that turns the test red, or `none`
   - the reach finding

4. **Settle by mutation.** If reading the code cannot settle whether a mutant turns the test red: apply the mutant, run that single node ID, restore the line, then view the file and confirm it matches the original byte for byte. Do all of that before moving to the next row.
   *Done when* no row has an unsettled mutant and every product file matches its original content.

5. **Report.** Put the ledger in your reply using exactly the shape of the anchor below, ordered by node ID, then add a final line `REAL: <n> · JUNK: <m>`.

```markdown
| Test | Verdict | Contract | Mutant killed | Refactor that turns it red | Reach |
|---|---|---|---|---|---|
| `tests/unit/test_account.py::test_withdraw_rejects_overdraft` | REAL | Withdrawing more than the balance raises and leaves the balance unchanged | `account.py:42` `raise Overdraft()` → `pass` | none | public `withdraw()`, same outcome both runs |
| `tests/unit/test_cli.py::test_help_mentions_usage` | JUNK | Pins an outcome: help text contains "Usage" | none — the text is a constant, so no logic sits between the source and the assertion | reword the help text | public `--help`, same outcome both runs |
```
