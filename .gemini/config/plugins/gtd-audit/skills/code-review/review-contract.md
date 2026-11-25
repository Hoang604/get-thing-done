# Code Review Contract

A **blind** review judges code solely by what the repository proves across the **review scope**: the target named by the user (or uncommitted changes, or the last commit if none are named, or the whole repository when asked for a repo audit) plus the code in the repository that directly impacts it or is directly impacted by it. Only the target modules are judged as reviewed modules; impacting and impacted code is context used to verify assumptions and consequences.

## Evidence and Origin Test

For each `VIOLATED` candidate, derive the verdict and fix strictly in the three ordered steps below before emitting the finding entry (never draft a fix first and backfill its justification):

1. **Classify the candidate**: determine whether resolving it (a) modifies or deletes existing code `X`, (b) adds a missing guard, validation, bound, or release (**omission**), or (c) depends on a rule, caller, or deployment load outside the repository (**external assumption**).
2. **Prove from the repository**:
   - For **(a) existing code `X`**: run the **Counterfactual Origin Test**—mentally remove or simplify `X` and trace impacting and impacted code to establish the original problem `P0` that `X` addressed, and whether `P0` is unreachable, handled elsewhere, or handled while violating a review principle.
   - For **(b) omission**: omit `Origin (P0)` and trace the concrete **Entry & Trigger** path from an external or internal caller to the unguarded sink and its deterministic consequence.
   - For **(c) external assumption**: state the two concrete outcomes depending on the external condition.
3. **Derive verdict and fix**:
   - Drop **(a)** when `P0` reaches `X` and `X` handles it without violating any principle.
   - Record **(c)** under **Open Questions** splitting both outcomes; never guess a Finding.
   - Record confirmed **(a)** or **(b)** as a Finding (no concrete reachable case, no finding) and derive the smallest fix strictly from Step 2—for **(a)**, the fix must still preserve valid `P0` behavior when `P0` remains reachable.

*Completion criterion*: every emitted Finding and Open Question follows its Step 1 classification and Step 2 proof in order, and no candidate was turned into a Finding without a concrete reachable case from the repository.

## Severity

Judge each confirmed finding by its blast radius across calls, data integrity, availability, and future edits:

| Level | Alert | Condition proven by the code |
|---|---|---|
| **Critical** | `> [!CAUTION]` | Damage escapes a single call and persists or propagates across independent users or requests: unauthorized access, cross-tenant exposure, code execution in a trusted origin, secret forgery, shared-process termination, or persisted/access-controlled state corruption without failing |
| **Major** | `> [!WARNING]` | Contained failure, bounded degradation, or multi-part change hazard: a defect contained within the triggered flow, a security weakness narrowing defense without direct persistent takeover, sustained resource/hot-path degradation under expected load, or a design/clarity defect coupling multiple sites or independent responsibilities |
| **Minor** | `> [!NOTE]` | Localized maintainability, readability, or cleanup defect confined to one cohesive unit and responsibility where every call executes honestly and safely |

## Report Format

Write findings in plain, direct language (explaining any technical term the first time it appears) so a reader unfamiliar with the codebase understands what the code does, why each defect occurs, and how to fix it in one read. Prefer fixes that delete code, flatten or separate tangled logic directly, and enforce invariants at the owning producer or entry boundary.

Every file, symbol, and line range is a clickable link with an absolute `file://` path and the file's basename as link text, never wrapped in backticks: [notes.py:L10-24](file:///abs/path/src/notes.py#L10-L24).

Subagent reports number findings `S-1, S-2, ...` (`security-reviewer`) or `A-1, A-2, ...` (`architecture-perf-reviewer`) and include a `Coverage` table (`FULL` / `NOT READ`) plus `Status: COMPLETE / STOPPED (partial coverage)`. The coordinator's merged report numbers findings sequentially (`1, 2, ...`) across all severity groups following the anchor below:

```markdown
### Code Review Report

**What this scope does & assumed load:** <Two or three sentences explaining what the reviewed code does and the load assumed from the repository.>

#### Critical

> [!CAUTION]
> **1. Orders close on the wrong calendar day** ([close_day.py:L40-52](file:///abs/path/billing/close_day.py#L40-L52))
> - **What this is:** At midnight this job closes the day and bills every unbilled order from that date.
> - **Problem & trigger (`Runtime Correctness and Concurrency`):** `close_day()` takes today's date from `datetime.utcnow().date()` while [create_order:L18](file:///abs/path/billing/orders.py#L18) stores timestamps in `Europe/Berlin`. An order placed at 00:30 Berlin time is billed under the previous day.
> - **Origin (`P0`):** Written to batch orders by calendar day, assuming server UTC matched the shop's local day.
> - **Fix:** Compute the cutoff date in the shop's timezone: `datetime.now(ZoneInfo("Europe/Berlin")).date()`.
> - **If we skip it:** Orders between 00:00 and 02:00 local time land on the wrong invoice date and require manual accounting correction.

#### Major

> [!WARNING]
> **2. Export endpoint reads unbounded request body** ([export.py:L14-29](file:///abs/path/billing/export.py#L14-L29))
> - **What this is:** Accepts filter JSON to generate an invoice CSV export.
> - **Problem & trigger (`Adversarial Fault Isolation and Cost Ordering`):** `request.json()` buffers the entire incoming payload without a byte cap before verifying the session header.
> - **Entry & Trigger:** An unauthenticated `POST /api/export` with a 500 MB JSON body exhausts worker heap before authentication rejects the call.
> - **Fix:** Authenticate from the `Authorization` header first and cap body reads at 64 KiB.
> - **If we skip it:** Any unauthenticated caller can OOM the billing worker with a handful of concurrent requests.

#### Open Questions
<!-- Omit when none exist. -->
- **Q-01** ([sync.py:L88-95](file:///abs/path/workers/sync.py#L88-95)):
  - If the worker runs as a single process: the in-memory lock holds.
  - If multiple worker processes run concurrently: two workers can process the same webhook batch twice.

#### Summary
- **Verdict:** <Healthy. Ship. | Fix 1 and 2 first.>
- **Lean:** `-<N> lines, -<M> dependencies possible.` <!-- Omit when no findings delete code or dependencies. -->
- **Not checked:** <Paths or runtime checks not read or executed with missing lens `(security | architecture-perf | both)` and remaining risk. | None (full scope read).>
```
