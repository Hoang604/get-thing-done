---
name: code-review
description: take scope, review code, return report
disable-model-invocation: true
---

A **blind** review judges code solely by what the repository proves across the **review scope**: the target named by the user (or uncommitted changes, or the last commit if none are named, or the whole repository when asked for a repo audit) plus the code that directly impacts it or is directly impacted by it. Record a defect proven across this scope as a Finding; when a verdict depends on a rule, caller, or deployment load outside the repository, record it as an Open Question splitting both outcomes.

## Principles

Every finding violates one of four orthogonal principles:

- **Runtime**: Step through the target with the inputs, concurrent timings, and expected load inferred from the repository, following each branch to the code impacted by its return value or state changes. Violated whenever a reachable execution under that load produces a result or state contradicting what impacted code relies on, exits without releasing an acquired resource, or exceeds the time or memory the expected load sustains.
- **Integrity**: Trace every value, type, and state transition entering, crossing, or leaving the target. Violated whenever code conceals or weakens a runtime invariant instead of enforcing it at its owning producer or entry boundary—suppressing a failure or treating an unverified state or value as valid, or performing a state transition its interface does not make explicit to callers.
- **Entropy**: Apply the **Day-One Test** across the target and the repository: compare what exists in the target against the single canonical form present requirements alone would produce. Violated whenever any part of the target owes its existence to the code's past rather than present requirements, or requires maintaining structure whose deletion (verifying zero remaining references via `rg` before claiming anything is unused), collapse, or replacement with a canonical primitive already available in the repository or platform preserves every reachable behavior with less code or fewer concepts without exposing tests to external I/O.
- **Clarity**: Read each target unit linearly from the perspective of an engineer modifying one responsibility. Violated whenever a reader cannot determine what the unit does and safely change one responsibility from a direct linear read—because unrelated responsibilities are interleaved inside it or the written code obscures or contradicts its actual behavior—and restructuring it restores direct readability without introducing shallow indirection.

## Severity

For each finding, judge its blast radius across calls, data integrity, and future edits:

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Damage escapes a single call and persists or propagates silently: a `Runtime` failure leaving persisted or process-wide state damaged or exposed for subsequent independent calls, or an `Integrity` violation allowing invalid or missing state to corrupt persisted or access-controlled data without failing |
| **Major** | `> [!WARNING]` | Contained failure or multi-part change hazard: a `Runtime` failure contained within the triggered call, an `Integrity` violation concealing invalid state within a call flow without corrupting persisted or access-controlled data, or an `Entropy` or `Clarity` defect coupling multiple sites or independent responsibilities so changing one behavior requires coordinated edits or risks breaking an unrelated one |
| **Minor** | `> [!NOTE]` | Localized `Entropy` or `Clarity` defect confined to one cohesive unit and responsibility: every call executes honestly and safely, and the cost falls only on local readability or cleanup |

## Dependency Classes

Every proposed change that moves or removes a boundary classifies the dependency behind it by what it touches at runtime:

1. **In-process**: computation or state in memory with no I/O. Merge into a deep module and test directly through its public interface, with no seam and no tests targeting absorbed internal layers.
2. **Local-substitutable**: local I/O or a store with a stand-in that runs inside the test suite. Keep the seam internal and run tests against the stand-in.
3. **External I/O**: a boundary crossing outside the local test environment. Isolate behind a port with a production adapter and an in-memory fake in tests.

## Steps

1. **Read scope**: Infer the expected load from the repository, then read the target together with the code in the repository that directly impacts it or is directly impacted by it (grepping every caller when a signature, return value, or behavior changes). Only the target modules are judged as reviewed modules; the impacting and impacted code is context used to verify assumptions and consequences. **When** the scope is bounded by a budget that can expire before full coverage, read the paths that accept external input and mutate or expose persisted or process-wide state first, and record any unread paths for `Not checked:`.
   - *Completion criterion*: the expected load is inferred, and every target module and all files in the repository that directly impact it or are directly impacted by it have been read (or, under a bounded budget, the paths mutating or exposing persisted or process-wide state from external input are read in full and all unread paths are listed).
2. **Analyze**: Judge every target module individually under all four principles (`Runtime`, `Integrity`, `Entropy`, `Clarity`) without pausing for user confirmation. Evaluate each candidate issue `X` individually while holding other candidates fixed, locating the exact lines and establishing:
   - How the surrounding flow normally works, and the concrete case in scope that proves the defect and its consequence. No concrete case, no finding.
   - **Counterfactual Origin Test**: Mentally remove or simplify `X` and trace what impacts `X` and what `X` impacts to identify the problem `P0` that `X` was written to address. Record `X` as a **Finding** only when the code in scope proves what `P0` was and shows either that `P0` is no longer reachable or is already handled elsewhere (making `X` redundant or transition residue), or that `X`'s current form handles `P0` in a way that violates `Runtime`, `Integrity`, `Entropy`, or `Clarity`; when whether `P0` can occur depends on a rule or caller outside the repository, record `X` under **Open Questions** splitting both outcomes; when `P0` reaches `X` and `X` handles it without violating any of the four principles, drop the candidate.
   - Its severity (`Critical`, `Major`, `Minor`) and the smallest fix and test update according to its dependency class, preferring fixes that delete code, flatten or separate tangled logic directly, and enforce invariants at the owning producer or entry boundary—never adding indirection or machinery the problem does not need.
   - *Completion criterion*: every target module has been judged under all four principles, and every finding has its normal flow, concrete trigger and consequence, `P0` origin and why `X` fails or is redundant, severity, and smallest fix with line links.
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
- **Lean:** `-<N> lines, -<M> dependencies possible.` <!-- Omit when no findings delete code or dependencies. -->
- **Not checked:** <Paths or runtime checks not read or executed, and the risk that leaves. | None (full scope read).>
```
