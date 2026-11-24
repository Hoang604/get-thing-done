---
name: test-increment
description: Design REAL boundary tests for an active plan produced by boundary-plan and embed them into each milestone and the Verification Matrix.
disable-model-invocation: true
---

**When** designing tests for an active plan (`implementation_plan.md` or `implementation_plan_round_<N>.md`), read `../test-triage/references/real-test-standard.md` to apply the four REAL-test rules and the whole-test verdict.

Every test you add to the active plan must earn a **REAL** verdict under that standard, and every existing test that breaks under a milestone's boundary change or fails the Day-One Test must be retired in that milestone.

## Steps

1. **Verify finalized plan, map milestones, and inspect existing tests.** Read the active plan (`implementation_plan.md` or `implementation_plan_round_<N>.md`—its `Users, Jobs & Use Scenarios` tables `S-xx` and `I-xx`, every `### Milestone N` section, and `### Verification Matrix`). **When** the active plan still contains `## Open Investigations` or any `[OPEN: ...]` marker, stop immediately and report that the plan must be finalized before adding a `Test Matrix`. Otherwise, read the existing test files covering the files in each milestone's `File Manifest` with `read_file`:
   - Search the workspace test suite with `rg` for every symbol in Milestone $N$'s `Retired Forms` (including any pre-change exposure hidden inside the boundary) and every symbol mutated in its `File Manifest`, and mark for deletion every existing test that relies on any property of the mutated code not guaranteed by Milestone $N$'s `Observable Outcome` and `Literal Contracts & Bound Structures`. Never rewrite such a test in place; cover Milestone $N$'s contracts with new REAL tests in `Test Matrix`.
   - For each Milestone $N$, derive every planned test forward from Milestone $N$'s `Acceptance Signal` (`S-xx`, `I-xx`), `Observable Outcome`, and `Literal Contracts & Bound Structures`—never by narrowing the contract to fit an assertion: specify the concrete `Input & Assertion` before checking Rules 1–4, then try to falsify that test with a promise-violating outcome or plausible mutation of that rule's logic that stays green across the milestone's tests, and with a promise-preserving refactor that turns it red. Admit a row into `Test Matrix` only after tightening its input and assertion until neither counterexample exists and both `Surviving mutant` and `Refactor that turns it red` are verified as `none`.
   *Done when* the active plan has zero `## Open Investigations` or `[OPEN: ...]` markers, every existing test that blocks Milestone $N$'s transition is mapped to the `Retired Form` or refactor in Milestone $N$ that it blocks, every `[MODIFY]` test file's exact target lines have been read, and every milestone's contract rules are mapped to planned tests with all six fields verified:
   - the product-derived contract sentence
   - the concrete input and assertion
   - the mutant killed (`file:line` old → new for existing lines, or `<file>::<symbol>` behavior → mutation for unwritten code)
   - the surviving mutant verified as `none` after falsification
   - the refactor that turns it red verified as `none` after falsification
   - the reach path

2. **Update the active plan.** Edit the active plan file directly (preserving its `ArtifactMetadata`):
   - In each `### Milestone N`, record every deleted test in `Retired Forms`, update `#### File Manifest` (`[NEW]`, `[MODIFY]` with clickable `[basename](file:///path#L<start>-L<end>)` spanning the exact mutated lines, `[DELETE]`) for all touched test files, and add or update a `#### Test Matrix` subsection (including its `Deleted Tests` table) formatted to the anchor below.
   - In `### Verification Matrix`, update `Baseline Checks` with the exact workspace test runner commands covering the test files across all milestones.
   *Done when* every `### Milestone N` in the active plan contains its `#### Test Matrix` formatted to the anchor below with `Surviving mutant` and `Refactor that turns it red` both verified as `none` on every REAL test row and every deleted test listed in `Deleted Tests` and `Retired Forms`, `#### File Manifest` lists every created, modified (with exact `#L<start>-L<end>` range), or deleted test file, and `### Verification Matrix` includes the exact test runner commands.

```markdown
#### Test Matrix

| Test | Contract | Input & Assertion | Mutant killed | Surviving mutant | Refactor that turns it red | Reach |
|---|---|---|---|---|---|---|
| `tests/test_note_store.py::test_save_assigns_id_and_persists_draft` | Saving a draft persists its title and body and returns the saved note with its assigned id | `save(NoteDraft(title="A", body="B"))` → returned `SavedNote` has non-empty `id`, `title == "A"`, `body == "B"`, and querying store by `id` returns identical `SavedNote` | `note_store.py::save` persist draft to store → return `SavedNote` without persisting | none | none | public `save(NoteDraft)`, read back via public query contract or local store stand-in |

| Deleted test | Transition blocked |
|---|---|
| `[test_notes.py::test_save_note_with_custom_store](file:///tests/test_notes.py#L14-L28)` | Calls retired `save_note(title, body, store=None)` at `notes.py:52` |
```
