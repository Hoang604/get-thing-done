---
name: test-increment
description: Design REAL boundary tests for an implementation_plan.md produced by boundary-plan and embed them into each milestone and the Verification Matrix.
disable-model-invocation: true
---

Every test you add to `implementation_plan.md` must earn a **REAL** verdict under all four rules, and every existing test that breaks under a milestone's boundary change or fails the Day-One Test must be retired in that milestone:

1. **Contract.** The test guards a rule that the code under test promises to whoever calls it or reads its output, and the rule holds for every valid input. State that promise in one sentence that quotes none of the test's literal values and leaves no room for an output that satisfies the sentence while breaking what a caller of that behavior relies on. If the only sentence you can write repeats the test's expected value, the test pins an outcome, not a contract.

2. **Kills a mutant.** Name a plausible edit to one product line (`file:line`, old → new) in the milestone's planned product code that breaks the rule in 1, where product logic carries the change to an assertion and turns it red, and that no other REAL test in scope already kills just as directly. Every part of the outcome that the rule in 1 determines for this test's input must be checked by an assertion, so that no plausible edit to a product line can violate the rule in 1 on this input and still leave the test green (a **surviving mutant**). If the values being compared travel from the test's setup to its assertion without passing through any product decision, no product mutant can reach that assertion.

3. **Survives refactors.** Every edit that keeps the contract leaves the test green. Each assertion may observe only what the contract promises. Anything else it observes is something a refactor is allowed to change.

4. **Reaches the product.** The test enters the product the same way its real callers do, starts from state the real path can produce, and gets the same outcome on every run in the tier where it is filed. Stand-ins are used only at out-of-process boundaries that cannot run locally in the test tier, and each stand-in implements the boundary's stateful contract rather than recording calls.

## Steps

1. **Map milestones and existing tests.** Read the active `implementation_plan.md` (its `Users, Jobs & Use Scenarios` tables `S-xx` and `I-xx`, every `### Milestone N` section, and `### Verification Matrix`) along with the existing test files covering the files in each milestone's `File Manifest`.
   - For each existing test that depends on a pre-change form or asserts internal details retired by Milestone $N$, record its fate (`deleted` or `rewritten`) in Milestone $N$'s `Retired Forms` and `File Manifest`.
   - For each Milestone $N$, derive the tests required to guard its `Acceptance Signal` (`S-xx`, `I-xx`) and `Literal Contracts & Bound Structures` so every contract rule introduced or modified by Milestone $N$ is covered by a test that satisfies all four REAL rules.
   *Done when* every obsolete existing test is assigned a fate in the milestone that retires its form, and every milestone's contract rules are mapped to planned tests with all five fields filled in:
   - the contract sentence
   - the mutant killed as `file:line` old → new
   - the surviving mutant (`none`)
   - the refactor that turns it red (`none`)
   - the reach path

2. **Update `implementation_plan.md`.** Edit `implementation_plan.md` directly:
   - In each `### Milestone N`, update `Retired Forms` and `#### File Manifest` (`[NEW]`, `[MODIFY]`, `[DELETE]`) for all touched test files, and add or update a `#### Test Matrix` subsection formatted to the anchor below.
   - In `### Verification Matrix`, update `Baseline Checks` with the exact workspace test runner commands covering the test files across all milestones.
   *Done when* every `### Milestone N` in `implementation_plan.md` contains its `#### Test Matrix` formatted to the anchor below with `Surviving mutant` and `Refactor that turns it red` both equal to `none` on every row, `#### File Manifest` lists every created, modified, or deleted test file, and `### Verification Matrix` includes the exact test runner commands.

```markdown
#### Test Matrix

| Test | Contract | Mutant killed | Surviving mutant | Refactor that turns it red | Reach |
|---|---|---|---|---|---|
| `tests/test_note_store.py::test_save_assigns_id_and_persists_draft` | Saving a draft persists its title and body and returns the saved note with its assigned id | `note_store.py:24` `repo.insert(draft)` → `SavedNote(id=1, title=draft.title, body=draft.body)` | none | none | public `save(NoteDraft)`, read back via `NoteRepository` |
```
