---
name: execute
description: Execute an approved implementation plan
---

## Scope & Blocker Rules

- **When** complying with the plan's declared contracts, invariants, and retired-form removals requires editing a file outside `File Manifest` and the plan with the codebase leaves zero design choices open, apply that edit and record the file and reason under `Round 0 — Build Deviations` in `implementation_ledger.md`.
- **When** satisfying the plan requires an unstated design choice, or when a declared contract or invariant cannot hold against the codebase, stop execution immediately and report the blocker to the user; never modify or relax a declared contract, invariant, or test to make a check pass.
- **When** execution reveals a capability serving a job outside the plan's declared users' jobs, leave it unimplemented and note it in the final reply.

## Implementation Ledger

Create `implementation_ledger.md` beside `implementation_plan.md` when Build starts, and keep completed round entries intact as later entries are added. Write `None` when a list entry has no items, and `None given` when a user gives no reason.

- `Round 0 — Build Deviations`: files modified outside `File Manifest` during Build and the reason.
- `Round <N>`: appended after each audit round with the audit report link, verdict, `Remediations`, and `Rejections`.
- `User Direction`: **when** the user interrupts execution and overrides how it proceeds, append what the user directed (written to be understood without the conversation) and the user's stated reason.
- `Verification`: appended once baseline checks and any declared audit gate pass, recording `Baseline Checks`.

```markdown
- **Round 0 — Build Deviations**:
  - [test_startup.py](file:///path/to/tests/test_startup.py#L14-L18): Replaced retired `LegacySettings("localhost", 8080)` call with `AppConfig(host="localhost", port=8080)`
- **User Direction** (Build milestone 2):
  - **Directed**: Keep `legacy_export.csv` reader until external billing cutover; omit `legacy_export.py` deletion from Milestone 2
  - **Reason**: External billing cron reads `legacy_export.csv` until Friday
- **Round 1**:
  - **Audit Report**: [audit_report_round_1.md](file:///path/to/audit_report_round_1.md)
  - **Verdict**: `FAIL (CLOSED)`
  - **Remediations**: `F-02 [CLOSED]` -> Removed unused `import legacy_sync` at [sync.py:12](file:///path/to/sync.py#L12)
  - **Rejections**: `F-01 [PLAN VETO]` -> `sync_state` at [sync.py:40](file:///path/to/sync.py#L40) computes in-memory state with zero network I/O
- **Verification**:
  - **Baseline Checks**: `python3 -m unittest` -> `Ran 24 tests in 0.12s — OK (exit code 0)`
```

## Execution Steps

1. **Build**: Read the `File Manifest` targets across the milestones (expanding reads only where needed for full function bodies, callers, or unlisted retired forms) and write their changes to disk. As each milestone's changes land, notify the user, then proceed immediately without pausing.
   - *Completion criterion*: Every milestone's `File Manifest` changes and required unlisted-file edits are written to disk, and `Round 0 — Build Deviations` in `implementation_ledger.md` is complete.

2. **Verify & Remediate**: Run the `Baseline Checks` declared across the active plan chain. **When** the plan declares a `Subagent Spawn Directive`, dispatch `boundary-auditor` with the directive's exact prompt (`<plan-link>` set to the active plan, `<ledger-link>`, and round `1`), read the `audit_report_round_<N>.md` path it returns, check every finding individually against the codebase, the active plan chain, and any `User Direction` in the ledger before editing any file, output a round summary stating the verdict and whether each finding **holds**, **fails**, or **partly holds** with the deciding `file:line` and plan requirement, and proceed immediately without pausing (`Audit Budget` counts total audit rounds from the initial plan):
   - **When** any `PLAN VETO` finding **holds** or its veto claim **partly holds**, rule on each part of the veto claim against the global rules (the user-level `GEMINI.md`/`AGENTS.md`) and the project rules (the project-root `GEMINI.md`) individually while holding the other parts fixed: **when** a rule resolves a part, carry that part into the `OPEN` path below, recording the rule with its location and the ruling under `Remediations` in `Round <N>`; **when** the rule sets resolve a part differently, the project rule governs; **when** no rule resolves a part, record `Round <N>` in `implementation_ledger.md` and stop execution immediately, reporting that part to the user without editing code.
   - **When** no `PLAN VETO` part remains unresolved and any holding finding or part is `OPEN`:
     - **When** `Audit Budget` is exhausted (`N` has reached the initial plan's `Audit Budget`), record `Round <N>` in `implementation_ledger.md` and stop execution immediately (Hard Stop), reporting the unresolved findings without running `bug-classification`, drafting `implementation_plan_round_<N>.md`, or editing code.
     - **When** within `Audit Budget`, leave current workspace code untouched, record `Round <N>` in `implementation_ledger.md`, read and apply `bug-classification` skill to every holding finding or part (both `OPEN` and `CLOSED`), then read and apply `boundary-plan` to write `<Artifact Directory>/implementation_plan_round_<N>.md` beside the prior plan covering all holding findings together (`RequestFeedback: false`, starting at the top with a link to the prior plan and those findings). Execute `implementation_plan_round_<N>.md` immediately through Step 1 (recording every modified file and any deviation under `Remediations` in `Round <N>` of `implementation_ledger.md`), run `Baseline Checks` across the active plan chain, then dispatch `boundary-auditor` with `<plan-link>` set to `implementation_plan_round_<N>.md` for Round $N+1$ **when** any holding finding or part in this round produces wrong behaviour in the application or the executed round plan's changes produce wrong behaviour in the application; **when** neither produces wrong behaviour, the audit gate is complete once `Baseline Checks` pass and every site the round plan changed is traced as behaviour-neutral, recorded under `Remediations` in `Round <N>`.
   - **When** no `PLAN VETO` part remains unresolved and zero `OPEN` findings or parts hold:
     - Remediate directly only every holding `CLOSED` finding or part strictly to its specified target state (without running `bug-classification` or creating a new plan), recording each fix with `file:line` under `Remediations` and each failing claim under `Rejections` in `Round <N>` of `implementation_ledger.md`.
     - **When** zero findings hold, or every holding `CLOSED` finding or part is remediated strictly to its specified target state without changing unrelated code, the audit gate is complete once `Baseline Checks` pass (re-run only if remediation edited files) and every scenario or invariant on remediated paths holds by test execution or code trace; **when** a fix changed code beyond a `CLOSED` finding's specified target state, dispatch `boundary-auditor` for Round $N+1$ if within `Audit Budget`, or stop immediately if `Audit Budget` is exhausted.
   - *Completion criterion*:
     - **On pass**: `Baseline Checks` pass, any declared audit gate is complete, `implementation_ledger.md` ends with `Verification`, and the reply delivers the link to `implementation_ledger.md` (and the final audit report when applicable), baseline check results, and any out-of-job notes.
     - **On Hard Stop** (Build blocker, unresolved holding `PLAN VETO`, or exhausted `Audit Budget`): `implementation_ledger.md` reflects all completed build/round entries without `Verification`, and the reply reports the exact blocker or unresolved findings with `file:line` and the ledger link.
