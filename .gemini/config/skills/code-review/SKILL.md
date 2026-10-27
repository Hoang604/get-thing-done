---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---

A **blind** review judges code solely by what the repository proves across the **review scope**: the target named by the user (or uncommitted changes, or the last commit if none are named, or the whole repository when asked for a repo audit) plus the code that directly impacts it or is directly impacted by it. Record a defect proven across this scope as a Finding; when a verdict depends on a rule, caller, or deployment load outside the repository, record it as an Open Question splitting both outcomes.

## Principles

Every finding violates one of two principles:

- **Runtime**: Step through the target with the inputs, concurrent timings, and expected load (inferred from the repository's entrypoints, README, and deploy/build config) its signature and deployment accept, following each branch to the code impacted by its return value or state changes. When a reachable execution under that load produces a result or state that contradicts what the impacted code expects, exits without releasing acquired state, or scales work or memory beyond what the expected load sustains, it violates Runtime.
- **Structure**: Mentally inline each boundary in the target into the code that uses or tests it, and compare its signature and body against the rest of the repository and the platform. When every reachable execution behaves consistently across the scope, yet crossing, keeping, or maintaining a boundary, duplicate, or unused symbol requires work that deleting it (once verified unreferenced across the whole tree via `rg`), replacing it with an existing repository or standard-library primitive, or tightening or realigning its signature to a single job eliminates without duplicating logic or exposing tests to external I/O, it violates Structure.

## Severity

For each finding, trace the triggered call to the moment it finishes, then test what happens to a subsequent, independent valid call:

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Runtime failure whose effect outlives the triggered call, leaving persisted or process-wide state damaged, exposed, or unrecovered when the next independent call runs |
| **Major** | `> [!WARNING]` | Runtime failure contained within the triggered call: that call fails, returns a wrong result, or stalls under the expected load, while persisted and process-wide state remain intact for the next independent call |
| **Minor** | `> [!NOTE]` | No runtime failure: every call executes correctly, and the cost falls only on working with the source code or its dependencies |

## Dependency Classes

Every proposed change that moves or removes a boundary classifies the dependency behind it by what it touches at runtime:

1. **In-process**: computation or state in memory with no I/O. Merge into a deep module and test directly through its public interface, with no seam and no tests targeting absorbed internal layers.
2. **Local-substitutable**: local I/O or a store with a stand-in that runs inside the test suite. Keep the seam internal and run tests against the stand-in.
3. **External I/O**: a boundary crossing outside the local test environment. Isolate behind a port with a production adapter and an in-memory fake in tests.

## Steps

1. **Read scope**: Identify the expected load from the repository's entrypoints, README, and deploy/build config, then read the target together with the code in the repository that directly impacts it or is directly impacted by it (grepping every caller when a signature, return value, or behavior changes). Only the target modules are judged as reviewed modules; the impacting and impacted code is context used to verify assumptions and consequences. **When** the scope is bounded by a budget that can expire before full coverage, read the paths that accept external input and mutate or expose persisted or process-wide state first, and record any unread paths for `Not checked:`.
   - *Completion criterion*: the expected load is identified, and every target module and all files in the repository that directly impact it or are directly impacted by it have been read (or, under a bounded budget, the paths mutating or exposing persisted or process-wide state from external input are read in full and all unread paths are listed).
2. **Analyze**: Judge every target module under both principles without pausing for user confirmation. For each candidate issue at location `X`, locate the exact lines and establish:
   - How the surrounding flow normally works, and the concrete input, timing, load, or boundary interaction in scope that triggers the failure or extra cost. No concrete case, no finding.
   - **Counterfactual Origin Test**: mentally remove `X` and trace what impacts `X` and what `X` impacts to identify the problem `P0` that `X` was written to address. Record `X` as a **Finding** only when the code in scope proves what `P0` was and shows either that the impacting code already prevents `P0` (making `X` redundant) or that `X` handles `P0` in a way that violates `Runtime` or `Structure` on the impacted code; when whether `P0` can occur depends on a rule or caller outside the repository, record `X` under **Open Questions** splitting both outcomes; when `P0` reaches `X` and `X` handles it without violating either principle, drop the candidate.
   - Its severity (`Critical`, `Major`, `Minor`) and the smallest fix and test update according to its dependency class, preferring fixes that delete code and never adding layers, frameworks, or config the problem does not need.
   - *Completion criterion*: every target module has been judged under both principles, and every finding has its normal flow, concrete trigger and consequence, `P0` origin and why `X` fails or is redundant, severity, and smallest fix with line links.
3. **Deliver report**: Write the report with `write_file` to `<appDataDir>/brain/<conversation-id>/<report-name>.md` in plain, direct language (explaining any technical term the first time it appears) following the anchor below so a reader unfamiliar with the codebase understands what the code does, why each issue exists, and how to fix it in one read. Number findings across all severity groups so the user can say "fix 1 and 3". Every file, symbol, and line range must be a clickable link with an absolute `file://` path and the file's basename as link text, never wrapped in backticks: [notes.py:L10-24](file:///abs/path/src/notes.py#L10-L24). Reply in chat with the clickable link to the report file and the count of findings per severity level.
   - *Completion criterion*: the report file exists on disk matching the anchor format and the chat reply gives its link and severity counts.

```markdown
### Code Review Report

**What this scope does & assumed load:** <Two or three sentences explaining what the reviewed code does and the load assumed from the repository.>

#### Critical

> [!CAUTION]
> **1. Orders close on the wrong calendar day** ([close_day.py:L40-52](file:///abs/path/billing/close_day.py#L40-L52))
> - **What this is:** At midnight this job closes the day and bills every unbilled order from that date.
> - **Problem & trigger (`Runtime`):** `close_day()` takes today's date from `datetime.utcnow().date()` while [create_order:L18](file:///abs/path/billing/orders.py#L18) stores timestamps in `Europe/Berlin`. An order placed at 00:30 Berlin time is billed under the previous day.
> - **Origin (`P0`):** Written to batch orders by calendar day, assuming server UTC matched the shop's local day.
> - **Fix:** Compute the cutoff date in the shop's timezone: `datetime.now(ZoneInfo("Europe/Berlin")).date()`.
> - **If we skip it:** Orders between 00:00 and 02:00 local time land on the wrong invoice date and require manual accounting correction.

#### Open Questions
<!-- Omit when none exist. -->
- **Q-01** ([sync.py:L88-95](file:///abs/path/workers/sync.py#L88-L95)):
  - If the worker runs as a single process: the in-memory lock holds.
  - If multiple worker processes run concurrently: two workers can process the same webhook batch twice.

#### Summary
- **Verdict:** <Healthy. Ship. | Fix 1 and 2 first.>
- **Lean:** `-<N> lines, -<M> dependencies possible.` <!-- Omit when no Structure findings delete code or dependencies. -->
- **Not checked:** <Paths or runtime checks not read or executed, and the risk that leaves. | None (full scope read).>
```
