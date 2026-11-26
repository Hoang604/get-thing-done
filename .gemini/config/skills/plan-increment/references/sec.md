# Security Increment

## Principles

Evaluate every concrete site in each affected milestone against six independent causal invariants:

1. **Verified Authority and Fail-Closed Boundaries:** Every authorization or boundary check derives solely from verified identity and fail-closed trusted configuration—denying execution when absent or invalid—and holds through the exact point where the protected operation executes or commits state.
2. **Input Structure and Execution Separation:** Untrusted data is verified from its actual content rather than caller claims and bound inertly so it remains passive data rather than executable or control state.
3. **Secret and Channel Protection:** Every secret stays confined to its owning trust domain across its full lifecycle—loaded solely from isolated secret storage and protected so no party outside that trust domain can read it directly or infer it from observable behavior.
4. **Fault Containment:** Any failure triggered across an untrusted boundary stays contained within the triggering execution rather than disrupting shared execution or holding shared state locked.
5. **Adversarial Work Bounding:** Entry boundaries verify caller authority for non-public operations and cap untrusted input and amplification before an untrusted caller can drive disproportionate work or resource consumption.
6. **External Dependency Integrity:** Every externally sourced dependency or artifact the system loads is immutably pinned and integrity-verified before execution.

## Viability Gates

Rule a site `amend` only when all four viability gates hold from the plan and inspected code:
- **Present:** The missing guard or flaw exists in a planned milestone contract or in touched codebase paths verified with `read_file`.
- **Live Exposure:** The flaw either ships in a deliverable or release pipeline, or compromises a live trust domain beyond unshipped local development and testing scaffolding.
- **Adversarial Reachability:** A party outside the owning trust domain—not code-only constants or operator-controlled configuration unless untrusted input reaches it—can trigger the path or observe its effect in a default or documented setup without a located guard closing it.
- **Unauthorized Gain:** That outside party obtains an outcome beyond what its starting authority already grants.

## Milestone Derivation & Anchor

For each milestone containing any site governed by the invariants above, inspect the relevant code with `read_file` and emit one individual ruling per site while holding the other sites fixed—ruling `no change` (citing the failing viability gate or existing guard) or `amend` (citing the violated invariant and the exact plan change required). Record the rulings in `#### Security Rulings` inside that milestone following the anchor below, and update every affected section of the active plan strictly from the `amend` rulings.

```markdown
#### Security Rulings

- `notes.py::NoteController.create` (Verified Authority and Fail-Closed Boundaries, Milestone 2): `owner_id` is read from the untrusted request body rather than server-verified auth context (Present, Live Exposure, Adversarial Reachability, Unauthorized Gain) → **amend** (derive `owner_id` exclusively from verified session context, remove `owner_id` from request schema, and add invariant `I-05`)
- `note_store.py::NoteDraft.title` (Input Structure and Execution Separation, Milestone 1): persisted via parameterized query binding in `NoteRepository.insert` → **no change** (Adversarial Reachability fails: bound parameter keeps title passive data)
```
