---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---

A **blind** review judges code solely by what the code itself shows. Intent, specs, commit messages, and author explanations are not inputs. Where a verdict depends on intent the code does not reveal, it becomes an Open Question instead of a finding.

## Vocabulary

- **Module**: anything with an interface and an implementation, at any scale.
- **Interface**: everything a caller must know to use the module correctly.
- **Implementation**: everything inside the module that callers do not need to know.
- **Depth**: how much behaviour sits behind each unit of interface. A **deep** module hides much behind little; a **shallow** module hides little behind much.
- **Seam**: a place where behaviour can be swapped without editing the code at that place.
- **Adapter**: a concrete implementation plugged into a seam.

## Principles

Every finding is a violation of one of two principles. Apply both to every module in scope and to every interaction across its seams.

### Structure Principle

> **Every module keeps what callers must know equal to what its signature states, hides as much behaviour as possible behind it, and absorbs change without edits outside itself.**

- **Leaks.** If correct use requires knowing anything the signature does not state, the interface leaks. Tests are callers too: a test that must know the implementation to pass shows a leak in the module or a test reaching past the interface.
- **The Deletion Test.** Imagine deleting the module. If complexity reappears across its callers, the module earns its place. If complexity collapses, the module is shallow.
- **Seams.** A seam earns its place only when at least two adapters plug into it, a test stand-in counting as one. A seam with a single adapter is speculative indirection.
- **Change.** Adding a variant of behaviour should land as new code beside existing code. A shape that forces edits to existing code or across callers for every new variant pushes the cost of change outward.

### Runtime Principle

> **Every cost the code incurs is bounded by the work it actually needs to do, and every failure surfaces where it happens.**

- **Cost.** For every cost the code incurs (time, memory, I/O, and anything it holds while working), trace what the cost grows with and how long it is held. A cost that grows with anything beyond what the work requires, or is held beyond the work that needs it, is a finding.
- **Failure.** A failure surfaces when, at the point it occurs, it becomes visible to the code able to handle it, in a form distinguishable from success. Any path on which a failure continues as if it were success is a finding.

## Severity

Assign each finding the first level whose condition the code evidence proves. A level the evidence only suggests is not proven.

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Data can be lost or corrupted, or a cost grows with input size or concurrency and nothing in the code bounds it |
| **Major** | `> [!WARNING]` | Behaviour is wrong, degraded, or fails under inputs or concurrency the code accepts, within a bound |
| **Minor** | `> [!NOTE]` | No runtime consequence; the cost falls on whoever reads, calls, tests, or changes the code |

## Dependency Classes

Every proposed change that moves a boundary classifies the dependencies it touches:

1. **In-process**: pure computation or in-memory state, no I/O. Merge into deep modules and test directly through the interface, with no seam.
2. **Local-substitutable**: has a local stand-in that runs inside the test suite. Keep the seam internal; tests run against the stand-in.
3. **Remote-owned**: a service the same owners run across a network boundary. A port at the seam, a network adapter in production, an in-memory adapter in tests.
4. **True-external**: a third-party service. An injected port, a mock adapter in tests.

When a change deepens a module, tests on the shallow layers it absorbs are replaced by tests at the new interface, not kept alongside them.

## Steps

### Phase 1: Discovery & Scoping

1. Receive the review target from the user.
2. Starting from the target's entrypoints, read the target, the modules it calls, the modules that call it, and the tests that exercise it, following each hop outward. Discovery is complete when one more hop adds no file needed to judge a module already in scope.
3. Output the scope as a table with columns `File | Role (target / dependency / caller / test) | Reason included`, every file as a link.
4. Ask the user: "Is scope complete?" and wait for confirmation before any analysis.

*Completion criterion*: the scope table is output and the user has confirmed it.

### Phase 2: Analysis & Reporting

1. Judge every module in scope under both principles. For every candidate finding, locate the exact lines and construct its Failure Mechanics from the code before recording it. A candidate whose mechanics cannot be constructed from the code is dropped, or recorded as an Open Question when it hinges on intent.
   - *Completion criterion*: every module in scope has a Structure verdict and a Runtime verdict, and every finding has Failure Mechanics with line links.
2. Write the report with `write_to_file` to `<appDataDir>/brain/<conversation-id>/<report-name>.md` in the exact Report Format. A report streamed into the chat response does not count.
   - *Completion criterion*: the report file exists and matches the Report Format.

The review changes no code; its only output is the report file.

## Report Format

Every file, symbol, and line range is a clickable link with an absolute `file://` path and the file's basename as link text, never wrapped in backticks: [basename.ext:L10-24](file:///absolute/path/to/basename.ext#L10-L24).

```markdown
### 1. Scope Reviewed

| Module | Structure | Runtime | Findings |
|---|---|---|---|
| [<module>](file:///...) | Sound / Findings | Sound / Findings | F-01, F-03 / — |

### 2. Strengths

<!-- Only what the code proves. If none qualifies: "None recorded". -->
- 🟢 **<Module>**: <What it does well, under which principle> ([basename.ext:Lx-y](file:///...))

### 3. Findings

<!-- Ordered by severity, Critical first. If none: "None". -->
> [!CAUTION]
> **F-01 · Critical · <Mechanism: the established name of the defect if one exists, otherwise a short name for its mechanism>**
> **Location:** [basename.ext:Lx-y](file:///...)
> **Principle:** Structure | Runtime
> **Failure Mechanics:**
> - **Normally:** <Behaviour under ordinary conditions>
> - **When & What:** <The condition, admitted by the code, under which it breaks, and exactly what happens>
> - **Why:** <Root cause mechanism>
> - **How:** <Concrete scenario that triggers it>

### 4. Open Questions

<!-- Verdicts that depend on intent the code does not reveal. If none: "None". -->
- [basename.ext:Lx-y](file:///...):
  - If the intent is <X>: the code is correct (<reason>).
  - If the intent is <Y>: the code is defective (<reason>).

### 5. Proposed Changes

| # | Resolves | Change | Dependency Class | Test Surface |
|---|---|---|---|---|
| P-01 | F-01, F-03 | <Change> | In-process / Local-substitutable / Remote-owned / True-external / — | <Where tests sit after the change, and which existing tests it replaces> |
```
