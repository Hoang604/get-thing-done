---
name: draft-plan
description: Draft formal implementation_plan.md artifact using EARS syntax with zero-prose literal contracts and seam test matrix
disable-model-invocation: true
---

# CORE DIRECTIVE

Translate an approved architectural proposal from `propose-plan` into a deterministic, zero-entropy `implementation_plan.md` Artifact.
Do not re-explore alternative designs. Enforce literal interface boundaries (`class` / `def` signatures with docstrings and type annotations) paired with explicit inline contracts (`invariants, error modes, data structures`). Never leak method bodies or line-by-line implementation code into the plan.

---

## 1. User Outcome & Risk Assessment

- Copy the exact **User Outcomes** block finalized and approved during `propose-plan`.
- Use GitHub-style alerts strictly to flag architectural boundaries and risks:
  - `> [!CAUTION]` for architecture shifts or data loss risks.
  - `> [!WARNING]` for breaking changes to public APIs or schemas.
  - `> [!IMPORTANT]` for critical load-bearing boundaries and invariants.
  - `> [!NOTE]` for minor side effects or operational gotchas.

---

## 2. Requirements (EARS Syntax & Seam Tracing)

Translate approved requirements strictly into EARS syntax structures:
- **Ubiquitous:** `The <system/component> shall <Action>.`
- **Event:** `When <Trigger>, the <system/component> shall <Action>.`
- **State:** `While <State>, the <system/component> shall <Action>.`
- **Unwanted:** `If <Condition>, then the <system/component> shall <Action>.`
- **Optional:** `Where <Feature>, the <system/component> shall <Action>.`

**Zero Orphan Requirements:** Every single EARS requirement must explicitly cite the exact clickable markdown link (`file://` with line anchor if modifying, or target path if new) of the target seam/interface that fulfills it (`e.g., -> Fulfills at [OrderService.process_order](file:///path/service.py#L45)`).

---

## 3. Design Definition (`Zero-Prose Literal Contracts & Seam Matrix`)

### A. Literal Interface Contracts (`Signatures & Inline Seam Contracts`)
For every target file to create (`[NEW]`), modify (`[MODIFY]`), or delete (`[DELETE]`), pinpoint exact line ranges using clickable [basename](file:///path#L10-L20) links without backticks and declare exact literal contracts:

- **Target Seam / Signature (`Literal Code & Inline Seam Contracts`):** Write the exact external boundary (`e.g., class, def, Pydantic fields, or config tables`) with docstrings and type annotations, using `...` (ellipses) to represent method bodies. For `[MODIFY]` targets, write ONLY the enclosing `class / def` signature and the specific attributes or contracts being modified (`e.g., def process(self, context: SpeechContext) -> None: """...""" ...`). Never write line-by-line implementation code inside this block.
- **Exact Caller Audit (`grep_search proof`):** Run `grep_search` across the workspace for this symbol. List every single caller file and exact line range (e.g., [caller.py:L10-L25](file:///path/caller.py#L10-L25)) that must be updated to match the new signature. If 0 callers exist outside tests, state: `"Caller Audit: 0 production callers found via grep_search."`
- **Invariants, Error Modes & Out-of-Seam State:** State exact invariants (`what must not change`), exact typed exceptions raised (`exceptions/return variants`), AND flag any out-of-seam state accessed directly (`e.g., os.environ keys or config tables read without parameter injection`).
- **Deep Implementation Strategy (`Private Helpers & Imports`):** State exact third-party imports (`e.g., librosa, urllib.request`), names of any private helper methods, and bullet points detailing the precise inline algorithmic strategy inside the method body (`e.g., loads audio via librosa.load(...), executes interleaved slices, replaces zero-sum frames`). Never leave inline modification mechanics unexplained.


### B. Seam Verification & Test Replacement Matrix (`Replace, Don't Layer`)
The interface is the test surface. Enforce a mechanical 4-column mapping table to trace test replacement across seams:

| Target Seam / Module | Old Shallow Test to `[DELETE]` | New Deep Test to `[CREATE/MODIFY]` | Test Stand-in / Adapter |
| :--- | :--- | :--- | :--- |
| [SymbolName](file:///path/target.py#L10-L40) | [old_test.py:L12-50](file:///path/old_test.py#L12-L50) | [new_seam_test.py:L10-60](file:///path/new_seam_test.py#L10-L60) | `LocalStandIn / Adapter` |

- **No Interface Leakage for Testing:** Never make private helper methods or internal seams public solely for unit test setup. Tests must assert on observable outcomes strictly through the module's external seam.

---

## 4. Verification & Validation Proof

Define mechanical, checkable proof of completion across the seam:
- **Verification Commands:** Exact terminal commands (`e.g., uv run pytest <target_test_file>`, `npm test`, lints, builds) executing against the target interfaces.
- **Validation Scenarios:** Step-by-step observable acceptance criteria or end-to-end user flows to verify success.
