---
name: test-increment
description: Design REAL boundary tests for an active plan produced by boundary-plan and embed them into each milestone and the Verification Matrix.
disable-model-invocation: true
---

Every test you add to the active plan (`implementation_plan.md` or `implementation_plan_round_<N>.md`) must earn a **REAL** verdict under all four rules, and every existing test that breaks under a milestone's boundary change or fails the Day-One Test must be retired in that milestone:

1. **Contract.** The test guards a rule that the code under test promises to whoever calls it or reads its output, and the rule holds for every valid input. State that promise in one sentence that quotes none of the test's literal values and leaves no room for an output that satisfies the sentence while breaking what a caller of that behavior relies on. If the only sentence you can write repeats the test's expected value, the test pins an outcome, not a contract.

2. **Kills a mutant.** Name a plausible product mutation in the milestone's code that breaks the rule in 1, where product logic carries the change to an assertion and turns it red, and that no other REAL test in scope already kills just as directly: cite `file:line` (`old → new`) when mutating an existing inspected line in a `[MODIFY]` file, or `<file>::<symbol>` (`planned behavior → broken mutation`) for `[NEW]` files or unwritten logic—never inventing line numbers for code not yet written. Every part of the outcome that the rule in 1 determines for this test's input must be checked by an assertion, so that no plausible product mutation can violate the rule in 1 on this input and still leave the test green (a **surviving mutant**). If the values being compared travel from the test's setup to its assertion without passing through any product decision, no product mutant can reach that assertion.

3. **Survives refactors.** Every edit that keeps the contract leaves the test green. Each assertion may observe only what the contract promises. Anything else it observes is something a refactor is allowed to change.

4. **Reaches the product.** The test enters and observes the product strictly through declarations that survived `Declaration Survival` in the milestone's `Literal Contracts & Bound Structures` (or the product's real external entrypoints and out-of-process stand-in state), starts from state the real path can produce, and gets the same outcome on every run in the tier where it is filed. Never invoke declarations hidden inside the boundary or retain/introduce an exported declaration solely for tests. Stand-ins are used only at out-of-process boundaries that cannot run locally in the test tier, and each stand-in implements the boundary's stateful contract rather than recording calls.

## Steps

1. **Verify finalized plan, map milestones, and inspect existing tests.** Read the active plan (`implementation_plan.md` or `implementation_plan_round_<N>.md`—its `Users, Jobs & Use Scenarios` tables `S-xx` and `I-xx`, every `### Milestone N` section, and `### Verification Matrix`). **When** the active plan still contains `## Open Investigations` or any `[OPEN: ...]` marker, stop immediately and report that the plan must be finalized before adding a `Test Matrix`. Otherwise, read the existing test files covering the files in each milestone's `File Manifest` with `read_file`:
   - Search the workspace test suite with `rg` for every symbol in Milestone $N$'s `Retired Forms` (including any pre-change exposure hidden inside the boundary) and every symbol mutated in its `File Manifest`, and mark for deletion every existing test that relies on any property of the mutated code not guaranteed by Milestone $N$'s `Observable Outcome` and `Literal Contracts & Bound Structures`. Never rewrite such a test in place; cover Milestone $N$'s contracts with new REAL tests in `Test Matrix`.
   - For each Milestone $N$, derive the tests required to guard its `Acceptance Signal` (`S-xx`, `I-xx`) and `Literal Contracts & Bound Structures` so every contract rule introduced or modified by Milestone $N$ is covered by a test that satisfies all four REAL rules.
   *Done when* the active plan has zero `## Open Investigations` or `[OPEN: ...]` markers, every existing test that blocks Milestone $N$'s transition is mapped to the `Retired Form` or refactor in Milestone $N$ that it blocks, every `[MODIFY]` test file's exact target lines have been read, and every milestone's contract rules are mapped to planned tests with all five fields filled in:
   - the contract sentence
   - the mutant killed (`file:line` old → new for existing lines, or `<file>::<symbol>` behavior → mutation for unwritten code)
   - the surviving mutant (`none`)
   - the refactor that turns it red (`none`)
   - the reach path

2. **Update the active plan.** Edit the active plan file directly (preserving its `ArtifactMetadata`):
   - In each `### Milestone N`, record every deleted test in `Retired Forms`, update `#### File Manifest` (`[NEW]`, `[MODIFY]` with clickable `[basename](file:///path#L<start>-L<end>)` spanning the exact mutated lines, `[DELETE]`) for all touched test files, and add or update a `#### Test Matrix` subsection (including its `Deleted Tests` table) formatted to the anchor below.
   - In `### Verification Matrix`, update `Baseline Checks` with the exact workspace test runner commands covering the test files across all milestones.
   *Done when* every `### Milestone N` in the active plan contains its `#### Test Matrix` formatted to the anchor below with `Surviving mutant` and `Refactor that turns it red` both equal to `none` on every REAL test row and every deleted test listed in `Deleted Tests` and `Retired Forms`, `#### File Manifest` lists every created, modified (with exact `#L<start>-L<end>` range), or deleted test file, and `### Verification Matrix` includes the exact test runner commands.

```markdown
#### Test Matrix

| Test | Contract | Mutant killed | Surviving mutant | Refactor that turns it red | Reach |
|---|---|---|---|---|---|
| `tests/test_note_store.py::test_save_assigns_id_and_persists_draft` | Saving a draft persists its title and body and returns the saved note with its assigned id | `note_store.py::save` persist draft to store → return `SavedNote` without persisting | none | none | public `save(NoteDraft)`, read back via public query contract or local store stand-in |

| Deleted test | Transition blocked |
|---|---|
| `[test_notes.py::test_save_note_with_custom_store](file:///tests/test_notes.py#L14-L28)` | Calls retired `save_note(title, body, store=None)` at `notes.py:52` |
```
