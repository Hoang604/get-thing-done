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
   - **Coverage derivation.** Before constructing `Test Matrix` for Milestone $N$, inspect each boundary declaration introduced or modified in Milestone $N$ across its declared interface, contracts, and ingress-to-sink dataflow to identify (1) every nominal promise it makes and (2) every assumption its nominal path relies on that nothing inside the boundary guarantees—each traced to the concrete contract, seam, or `file:line` where the boundary meets something outside its control. Emit the ruling on each identified item individually while holding the other items fixed (citing the milestone contract, seam, or `file:line`; grouping declarations or items into a shared ruling is invalid): for a nominal promise, state the planned test promise; for an assumption, state either `unreachable` (citing the structural fact that prevents it from breaking) or `reachable` with the invariant the boundary must enforce when it breaks—citing either the planned guard/contract or `unguarded`. When any `reachable` item is ruled `unguarded` (the active plan omits its contract or guard), stop immediately before editing the plan and report the milestone, boundary declaration, and unguarded assumption so the plan is updated first. Construct Milestone $N$'s `Test Matrix` strictly from these individual rulings.
   - **Per-test derivation.** For each planned test derived from Milestone $N$'s `Coverage Rulings` (alongside its `Acceptance Signal` `S-xx`, `I-xx`, `Observable Outcome`, and `Literal Contracts & Bound Structures`), evaluate it individually while holding the other planned tests fixed (grouping tests into a shared ruling is invalid)—never by narrowing the contract to fit an assertion: specify the concrete `Input & Assertion` before checking Rules 1–4, then try to falsify that test with a promise-violating outcome or plausible mutation of that rule's logic that stays green across the milestone's tests, and with a promise-preserving refactor that turns it red. Admit a row into `Test Matrix` only after tightening its setup and assertions until neither counterexample exists and both `Surviving mutant` and `Refactor that turns it red` are verified as `none`.
   *Done when* the active plan has zero `## Open Investigations` or `[OPEN: ...]` markers, every existing test that blocks Milestone $N$'s transition is mapped to the `Retired Form` or refactor in Milestone $N$ that it blocks, every `[MODIFY]` test file's exact target lines have been read, every boundary declaration in every milestone has individual, ungrouped `Coverage Rulings` for all of its nominal promises and external assumptions with zero `unguarded` reachable assumptions remaining, and every nominal and `reachable` ruling is mapped strictly to planned tests evaluated individually with all six fields verified:
   - the product-derived contract sentence
   - the concrete stimulus/setup and assertions
   - the mutant killed (`file:line` old → new for existing lines, or `<file>::<symbol>` planned behavior → broken mutation for unwritten code)
   - the surviving mutant verified as `none` after falsification
   - the refactor that turns it red verified as `none` after falsification
   - the reach path

2. **Update the active plan.** Edit the active plan file directly (preserving its `ArtifactMetadata`):
   - In each `### Milestone N`, record every deleted test in `Retired Forms`, update `#### File Manifest` (`[NEW]`, `[MODIFY]` with clickable `[basename](file:///path#L<start>-L<end>)` spanning the exact mutated lines, `[DELETE]`) for all touched test files, and add or update a `#### Test Matrix` subsection—opening with its individual `Coverage Rulings` followed by the `Test Matrix` table constructed strictly from those rulings and its `Deleted Tests` table—formatted to the anchor below.
   - In `### Verification Matrix`, update `Baseline Checks` with the exact workspace test runner commands covering the test files across all milestones.
   *Done when* every `### Milestone N` in the active plan contains its `#### Test Matrix` formatted to the anchor below—starting with individual, ungrouped `Coverage Rulings` covering every boundary declaration in the milestone, followed by a `Test Matrix` table constructed strictly from those rulings with `Surviving mutant` and `Refactor that turns it red` both verified as `none` on every REAL test row and every deleted test listed in `Deleted Tests` and `Retired Forms`—`#### File Manifest` lists every created, modified (with exact `#L<start>-L<end>` range), or deleted test file, and `### Verification Matrix` includes the exact test runner commands.

```markdown
#### Test Matrix

- **Coverage Rulings:**
  - `note_store.py::save(NoteDraft)` (nominal, Milestone 1 contract): persists draft and returns `SavedNote` with assigned `id` → `test_save_assigns_id_and_persists_draft`
  - `note_store.py::save(NoteDraft)` (assumption at store write seam: underlying store write succeeds) → `reachable` (guarded by transactional write contract in Milestone 1) → `test_save_leaves_store_unchanged_on_write_failure`
  - `note_store.py::save(NoteDraft)` (assumption at entry: `title` is non-empty) → `unreachable` (enforced by `NonEmptyStr` validated at Milestone 2 entry boundary)

| Test | Contract | Input & Assertion | Mutant killed | Surviving mutant | Refactor that turns it red | Reach |
|---|---|---|---|---|---|---|
| `tests/test_note_store.py::test_save_assigns_id_and_persists_draft` | Saving a draft persists its title and body and returns the saved note with its assigned id | `save(NoteDraft(title="A", body="B"))` → returned `SavedNote` has non-empty `id`, `title == "A"`, `body == "B"`, and querying store by `id` returns identical `SavedNote` | `note_store.py::save` persist draft to store → return `SavedNote` without persisting | none | none | public `save(NoteDraft)`, read back via public query contract or local store stand-in |

| Deleted test | Transition blocked |
|---|---|
| `[test_notes.py::test_save_note_with_custom_store](file:///tests/test_notes.py#L14-L28)` | Calls retired `save_note(title, body, store=None)` at `notes.py:52` |
```
