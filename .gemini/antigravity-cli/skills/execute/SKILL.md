---
name: execute
description: Execute an approved implementation plan
disable-model-invocation: true
---

## Adaptation, Scope & Completeness Rules

- **When** complying with the plan's contracts, invariants, and retired-form removals requires editing a file outside the `File Manifest` or adapting a declared contract, and the plan together with the codebase leaves only one way to write that edit, apply it and append the file and reason to `implementation_ledger.md` at once. **When** reaching a state that satisfies all of the plan's contracts and invariants requires a choice or value absent from the plan and codebase, or when the plan's contracts and invariants cannot hold together against the codebase, stop execution immediately and report the blocker to the user; never relax a declared contract, invariant, or test to make a check pass. **When** execution exposes a potential capability that serves a job outside the plan's declared users' jobs, leave the code unchanged and record it under `Out-of-Job Observations` in `Round 0` of `implementation_ledger.md`.
- **When** editing a function during Build or remediation, rewrite the whole body of that function so nothing remains in it that depends on the pre-change design. **When** a scenario, check, or audit finding fails on an input, fix the structural property that makes that class of inputs fail across every place in the subsystem that shares that property; never branch on the literal value that failed.

## Implementation Ledger

Create `<plan-dir>/implementation_ledger.md` when Build starts and only append to it: never edit or remove an entry.

- `Round 0 — Build Deviations`: records every file modified outside the plan's `File Manifest`, every declared contract adapted during Build, and any out-of-job observation.
- `Round <N>`: appended after each audit round with the report link, verdict, remediations, and rejections.
- `User Direction`: **when** the user interrupts execution and changes how it proceeds, append what the user directed (written so it reads without the conversation) and the reason the user gave (`None given` when omitted).
- `Verification`: appended once baseline checks and the audit gate pass.

```markdown
- **Round 0 — Build Deviations**:
  - [test_startup.py](file:///path/to/tests/test_startup.py#L14-L18): Replaced retired `LegacySettings("localhost", 8080)` call with `AppConfig(host="localhost", port=8080)` | `None (strict adherence to File Manifest)`
  - **Out-of-Job Observations**: Audit log for project views (serves security admin tracking outside declared users' jobs) | `None`
- **Round 1**:
  - **Audit Report**: [audit_report_round_1.md](file:///path/to/audit_report_round_1.md)
  - **Verdict**: `PASS` | `FAIL (CLOSED)` | `FAIL (OPEN)` | `PLAN VETO`
  - **Remediations**: `F-02 [CLOSED]` -> Removed unused `import legacy_sync` at [sync.py:12](file:///path/to/sync.py#L12) | `None`
  - **Rejections**: `F-01 [PLAN VETO]` -> `sync_state` at [sync.py:40](file:///path/to/sync.py#L40) computes in-memory state with zero network I/O | `None`
- **User Direction** (during Build milestone 2):
  - **Directed**: Keep `legacy_export.csv` reader until the external billing pipeline cutover; removes the `legacy_export.py` deletion from Milestone 2
  - **Reason**: External billing cron still reads `legacy_export.csv` until Friday | `None given`
- **Verification**:
  - **Baseline Checks**: `python3 -m unittest` -> `Ran 24 tests in 0.12s — OK (exit code 0)`
  - **Unplanned Decisions**: [config.py:18](file:///path/to/config.py#L18): Sorted exported keys alphabetically for deterministic snapshot comparison | `None`
```

## Execution Steps

1. **Build**: For each milestone $N$ in sequence, read only the `#L<start>-L<end>` slices in milestone $N$'s `File Manifest` whose `[MODIFY]` target lines are absent from current context, and write all of milestone $N$'s file changes to disk before reading or editing anything for milestone $N+1$. Upon completing milestone $N$, notify the user that milestone $N$ is finished, state what milestone $N+1$ will do (or state the transition to Verify & Remediate after the final milestone), and proceed immediately without pausing.
   - *Completion criterion*: Every milestone's `File Manifest` changes and required unlisted adaptations are written to disk, the full body of every touched function contains nothing from the pre-change design, and Round 0 of `implementation_ledger.md` is complete.

2. **Verify & Remediate**: Run the baseline check commands declared in the plan. **When** the plan declares a `Subagent Spawn Directive`, invoke `boundary-auditor` with the directive's exact prompt for Round 1 (`audit_report_round_1.md`) and the link to `implementation_ledger.md`. **When** an audit round returns, check each finding against the codebase and the plan before editing any file, output a round summary to the user stating the round's verdict and whether each finding **holds**, **fails**, or **partly holds** with the `file:line` and plan requirement that decided it, and proceed immediately without waiting for user input:
   - **When** any `PLAN VETO` finding **holds**, stop execution immediately and report it to the user without remediating.
   - Otherwise, remediate only what **holds** (recording each fix with its `file:line` under `Remediations` in `Round <N>` of `implementation_ledger.md`) and keep the code against what **fails** (recording each rejected claim with its `file:line` evidence under `Rejections`). **When** every holding finding is `CLOSED` and remediated to its exact specified target state (including when zero findings hold), the audit gate is complete once baseline checks and any scenarios or invariants on paths touched by remediation pass; **when** any holding finding is `OPEN` or a fix changes code beyond a `CLOSED` finding's specified target state, dispatch `boundary-auditor` for Round $N+1$ (or stop immediately if the `Audit Budget` is exhausted).
   Once verification and the audit gate pass, append the `Verification` entry to `implementation_ledger.md` and reply to the user with the link to `implementation_ledger.md` (and the final audit report when applicable), a summary of the delivered outcome and baseline check results, and any unplanned decisions, out-of-job observations, or unchecked risks.
   - *Completion criterion*: Baseline check commands pass, the audit gate (when declared) is complete with every scenario and invariant on remediated paths re-verified, `implementation_ledger.md` ends with the `Verification` entry (`Baseline Checks` and `Unplanned Decisions`), and the completion report with the ledger link is delivered to the user.
