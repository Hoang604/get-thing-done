---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---

A **blind** review judges code solely by what the repository proves across the **review scope**: the user-specified target plus the code that directly impacts it or is directly impacted by it. Record a defect proven across this scope as a Finding; when a verdict depends on a rule or caller outside the repository, record it as an Open Question splitting both outcomes.

## Principles

Every finding violates one of two principles:

- **Runtime**: Step through the target with the inputs and concurrent timings its signature accepts, following each branch to the code impacted by its return value or state changes. When a reachable execution produces a result or state that contradicts what the impacted code expects, or exits without releasing acquired state, it violates Runtime.
- **Structure**: Mentally inline each boundary in the target into the code that uses or tests it, and compare its signature against what its body requires. When every reachable execution behaves consistently across the scope, yet crossing or maintaining a boundary requires work that inlining or tightening the signature eliminates without duplicating logic or exposing tests to external I/O, it violates Structure.

## Severity

For each finding, trace the triggered call to the moment it finishes, then test what happens to a subsequent, independent valid call:

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Runtime failure whose effect outlives the triggered call, leaving persisted or process-wide state damaged or unrecovered when the next independent call runs |
| **Major** | `> [!WARNING]` | Runtime failure contained within the triggered call: that call fails or returns a wrong result, while persisted and process-wide state remain intact for the next independent call |
| **Minor** | `> [!NOTE]` | No runtime failure: every call executes correctly, and the cost falls only on working with the source code |

## Dependency Classes

Every proposed change that moves or removes a boundary classifies the dependency behind it by what it touches at runtime:

1. **In-process**: computation or state in memory with no I/O. Merge into a deep module and test directly through its public interface, with no seam and no tests targeting absorbed internal layers.
2. **Local-substitutable**: local I/O or a store with a stand-in that runs inside the test suite. Keep the seam internal and run tests against the stand-in.
3. **External I/O**: a boundary crossing outside the local test environment. Isolate behind a port with a production adapter and an in-memory fake in tests.

## Steps

1. **Read scope**: Read the user-specified target together with the code in the repository that directly impacts it or is directly impacted by it. Only the user-specified target modules are judged as reviewed modules; the impacting and impacted code is context used to verify assumptions and consequences.
   - *Completion criterion*: every target module and all files in the repository that directly impact it or are directly impacted by it have been read.
2. **Analyze**: Judge every target module under both principles without pausing for user confirmation. For each candidate issue at location `X`, locate the exact lines and establish:
   - How the surrounding flow normally works, and the concrete input, timing, or boundary interaction in scope that triggers the failure or extra cost.
   - **Counterfactual Origin Test**: mentally remove `X` and trace what impacts `X` and what `X` impacts to identify the problem `P0` that `X` was written to address. Record `X` as a **Finding** only when the code in scope proves what `P0` was and shows either that the impacting code already prevents `P0` (making `X` redundant) or that `X` handles `P0` in a way that violates `Runtime` or `Structure` on the impacted code; when whether `P0` can occur depends on a rule or caller outside the repository, record `X` under **Open Questions** splitting both outcomes; when `P0` reaches `X` and `X` handles it without violating either principle, drop the candidate.
   - Its severity (`Critical`, `Major`, `Minor`) and the fix and test update according to its dependency class, ensuring the fix resolves `P0` while removing `X`'s violation.
   - *Completion criterion*: every target module has been judged under both principles, and every finding has its normal flow, trigger and consequence, `P0` origin and why `X` fails or is redundant, severity, and fix with line links.
3. **Deliver report**: Write the report with `write_to_file` to `<appDataDir>/brain/<conversation-id>/<report-name>.md`, presenting all findings (ordered from Critical to Minor, with their context, failure mechanics, origin `P0`, and proposed fix) and open questions clearly so a reader unfamiliar with the codebase understands what the code does, why each issue exists, and how to fix it without having to cross-reference separate sections. Every file, symbol, and line range must be a clickable link with an absolute `file://` path and the file's basename as link text, never wrapped in backticks: [notes.py:L10-24](file:///abs/path/src/notes.py#L10-L24). Reply in chat with the clickable link to the report file and the count of findings per severity level.
   - *Completion criterion*: the report file exists on disk and the chat reply gives its link and severity counts.
