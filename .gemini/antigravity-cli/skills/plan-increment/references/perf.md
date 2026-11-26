# Runtime & Performance Increment

Infer the repository's production runtime profile from the codebase before evaluating any milestone.

## Principles

Evaluate every concrete site in each affected milestone against four independent principles (architecture integrity and entropy remain governed by `boundary-plan`):

1. **Runtime Correctness:** Every reachable execution branch under the inferred operating regime produces state consistent with what downstream code relies on.
2. **Concurrency and State Serialization:** Overlapping mutations to state shared across executions are serialized atomically so concurrent executions cannot race or clobber newer state.
3. **Bounded Resource Lifecycle:** Every dynamically held resource or unbounded state structure enforces an explicit capacity bound—with backpressure whenever producers can outpace consumers—and releases deterministically on every exit path.
4. **Work and Responsiveness Proportionality:** Under the inferred operating regime, executed work scales proportionally with the requested operation, and heavy or blocking work stays off shared latency-sensitive paths.

## Milestone Derivation & Anchor

For each milestone containing any site governed by the principles above, inspect the relevant code with `read_file` and emit one individual ruling per site while holding the other sites fixed—stating the inferred operating regime that governs it, whether the current plan yields `no change` (with the structural guarantee already closing it) or `amend` (with the exact change applied to the plan). Record the rulings in `#### Perf Rulings` inside that milestone following the anchor below, and update every affected section of the active plan strictly from the `amend` rulings.

```markdown
#### Perf Rulings

- **Inferred Operating Regime:** Concurrent API writers updating shared note storage; bursts up to hundreds of drafts per minute.
- `note_store.py::save(NoteDraft)` (Concurrency and State Serialization, Milestone 1): concurrent saves against the same storage handle can interleave partial writes → **amend** (serialize writes inside a single transaction in `NoteRepository.insert` and add concurrency invariant `I-04`)
- `note_store.py::list_recent(limit)` (Bounded Resource Lifecycle, Milestone 1): query enforces `limit <= 100` at the entry boundary → **no change** (upper bound already enforced by `PageLimit` contract)
```
