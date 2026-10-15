---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---

A **blind** review judges code solely by what the target modules and their 1-hop context show. Record a violation proven by the code itself as a Finding; when a verdict depends on a business rule or intent the code does not reveal, record it as an Open Question splitting both outcomes.

## Principles

Every finding is a violation of one of two principles. Apply both to every target module and to every interaction across its boundaries.

### Structure Principle

- **Leaks & Friction.** Everything required to use a module correctly is stated in its signature and return value. When a caller must know unstated ordering, hidden assumptions, or internal details, assemble multi-step state that belongs inside the boundary, suffer mutations to caller or global state outside the return contract, or reach into private internals from tests, the boundary leaks.
- **The Deletion Test.** Imagine deleting the module. When complexity reappears across its callers, the module earns its place; when complexity collapses, the module is shallow.
- **Seams.** A seam earns its place when at least two adapters plug into it, a test stand-in counting as one. A seam with a single adapter is speculative indirection.
- **Scattered Variation.** When two or more variants of behaviour already exist in scope and changing or adding one forces parallel edits across multiple functions or callers, the boundary fails to isolate variation. A single concrete behaviour with no seam is sound.
- **Entropy & Residue.** Every concept has one canonical representation and execution path, reusing existing codebase primitives. Any duplicate path, compatibility shim, reinvented utility, or form whose justification relies on the code's past rather than present requirements is transition residue.
- **Honest Types.** Every type states what a value always is: data the domain always needs is non-optional, an optional type exists only when absence is a real domain state, and no annotation or cast silences the type checker (`Any`, `# type: ignore`, unchecked assertions).

### Runtime Principle

- **Correctness & Dataflow.** Under every input, state, and concurrency interleaving the signature accepts, execution preserves domain invariants and carries every return value, state mutation, and emitted event to its terminal sink without loss, corruption, stall, or unhandled crash.
- **Boundary Integrity.** Outside data (user input, files, network, environment) is validated into strict types at entry; past entry, code passes valid data through unchanged or fails immediately on invalid data. Any fallback (`or default`, `??`, `if x is None`) that invents a substitute for missing required data—or applies a default inside domain logic instead of once at entry—is a finding.
- **Cost.** Every runtime cost (time, memory, I/O, locks, handles) is bounded by the work required and released as soon as that work finishes. Any cost that grows with an unbounded dimension or is held across work that does not need it is a finding.
- **Failure Surfacing.** Every failure becomes visible where it occurs to the code able to handle it, in a form distinguishable from every success state. Any path on which a failure continues as if it were success is a finding.

## Severity

Assign each finding the first level whose condition the code evidence proves.

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Data can be lost or corrupted, or a cost grows with input size or concurrency and nothing in the code bounds it |
| **Major** | `> [!WARNING]` | Behaviour is wrong, degraded, or fails under inputs or concurrency the code accepts, within a bound |
| **Minor** | `> [!NOTE]` | No runtime consequence; the cost falls on whoever reads, calls, tests, or changes the code |

## Dependency Classes

Every proposed change that moves a boundary classifies the dependency it touches by what the code shows:

1. **In-process**: pure computation or in-memory state, no I/O. Merge into a deep module and test directly through its interface, with no seam.
2. **Local-substitutable**: local I/O or a store with an in-process/local stand-in that runs inside the test suite. Keep the seam internal; tests run against the stand-in.
3. **External I/O**: a network service, external process, or hardware boundary. Isolate behind a port with a production adapter and an in-memory or fake adapter in tests.

When a change deepens a module, tests on the shallow layers it absorbs are replaced by tests at the new interface.

## Steps

1. **Read target & 1-hop context**: Read the target files or directories passed by the user, plus their direct callers, direct dependencies, and the tests that exercise them (1 hop outward) as context to inspect how each target module's interface, seams, and dataflow are used. Only the user-specified target modules are judged as reviewed modules; 1-hop files are context.
   - *Completion criterion*: every target module and its 1-hop callers, dependencies, and tests have been read.
2. **Analyze**: Judge every target module under both principles without pausing for user confirmation. For each candidate finding, locate the exact lines and construct its `Failure Mechanics` (`Normally`, `Trigger & Consequence`, `Why`) from the code: for Runtime findings, state the accepted input, state, or interleaving that breaks behaviour and what happens; for Structure findings, state the call, test, or change operation that incurs the cost or leak. Drop any candidate whose mechanics cannot be constructed from the code, or record it under `Open Questions` when it hinges on unstated intent.
   - *Completion criterion*: every target module has a Structure verdict and a Runtime verdict, and every finding has `Failure Mechanics` with line links.
3. **Deliver report**: Write the report with `write_to_file` to `<appDataDir>/brain/<conversation-id>/<report-name>.md` matching the Report Format below, then reply in chat with the clickable link to the report file and the count of findings per severity level.
   - *Completion criterion*: the report file exists on disk and the chat reply gives its link and severity counts.

## Report Format

Every file, symbol, and line range is a clickable link with an absolute `file://` path and the file's basename as link text, never wrapped in backticks: [notes.py:L10-24](file:///abs/path/src/notes.py#L10-L24).

```markdown
### 1. Scope Reviewed

| Module | Structure | Runtime | Findings |
|---|---|---|---|
| [notes.py](file:///abs/path/src/notes.py) | Findings | Findings | F-01, F-02 |
| [slug.py](file:///abs/path/src/slug.py) | Sound | Sound | — |

### 2. Strengths

<!-- Only what the code proves. If none qualifies: "None recorded". -->
- 🟢 **[slug.py](file:///abs/path/src/slug.py)**: Normalizes Unicode and enforces length bounds behind a single pure function with no leaked state ([slug.py:L12-34](file:///abs/path/src/slug.py#L12-L34))

### 3. Findings

<!-- Ordered by severity, Critical first. If none: "None". -->
> [!WARNING]
> **F-01 · Major · Silent Write Failure on Storage Timeout**
> **Location:** [notes.py:L42-55](file:///abs/path/src/notes.py#L42-L55)
> **Principle:** Runtime
> **Failure Mechanics:**
> - **Normally:** `save_note` writes the note payload to `store.put` and returns the saved `Note` record.
> - **Trigger & Consequence:** When `store.put` raises `TimeoutError`, the `except Exception` block at [notes.py:L51-54](file:///abs/path/src/notes.py#L51-L54) logs a warning and returns an unpersisted `Note` instance; caller [api.py:L28](file:///abs/path/src/api.py#L28) returns HTTP 201 Created while the note is lost.
> - **Why:** The catch block converts a storage failure into a normal return value indistinguishable from a persisted write.

> [!NOTE]
> **F-02 · Minor · Single-Adapter `NoteValidatorPort` Seam**
> **Location:** [notes.py:L15-29](file:///abs/path/src/notes.py#L15-L29)
> **Principle:** Structure
> **Failure Mechanics:**
> - **Normally:** `save_note` delegates title checking to an injected `NoteValidatorPort`.
> - **Trigger & Consequence:** Every caller and test ([test_notes.py:L18-25](file:///abs/path/tests/test_notes.py#L18-L25)) must construct and pass `DefaultNoteValidator`, which performs pure in-memory string checks with no second adapter anywhere in scope.
> - **Why:** Pure in-process validation is split behind an abstract interface with only one implementation, failing the Deletion Test and Seams rule.

### 4. Open Questions

<!-- Verdicts that depend on intent the code does not reveal. If none: "None". -->
- [notes.py:L60-66](file:///abs/path/src/notes.py#L60-L66):
  - If empty `body` strings are valid blank notes: the code is correct (`body: str` is stored verbatim).
  - If notes require non-empty content: `NoteDraft` lacks an entry check rejecting whitespace-only bodies.

### 5. Proposed Changes

| # | Resolves | Change | Dependency Class | Test Surface |
|---|---|---|---|---|
| P-01 | F-01 | Remove the `TimeoutError` catch in `save_note` so storage failures propagate to the caller | Local-substitutable | Assert `TimeoutError` propagation in [test_notes.py:L40-52](file:///abs/path/tests/test_notes.py#L40-L52) |
| P-02 | F-02 | Inline `DefaultNoteValidator` into `NoteDraft` construction and delete `NoteValidatorPort` | In-process | Replace validator mock setup in [test_notes.py:L18-25](file:///abs/path/tests/test_notes.py#L18-L25) with direct `save_note` calls |
```
