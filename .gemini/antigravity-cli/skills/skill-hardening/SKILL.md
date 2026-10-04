---
name: skill-hardening
description: Iteratively stress-test and harden a skill through N rounds of adversarial case generation, driving generality and eliminating checklists
disable-model-invocation: true
---

# Skill Hardening

Harden a target skill across $N$ iterations (default: 10) by pairing adversarial case generation against generative synthesis.

## Invariants

- **Immutable Source**: The target skill file is strictly read-only during execution. Write the hardened skill exclusively to `<Artifact Directory>/hardened_<skill_name>.md`. Never overwrite the source file without explicit user approval.
- **Diff Verification**: After each iteration, regenerate `<Artifact Directory>/<skill_name>_diff.patch` via `diff -u` so the diff is continuously available for review.
- **Monotonic Generality**: Across every iteration, principles may only become sharper and broader in coverage, never narrower. Escaped cases are authoring scaffolds: never add them into the skill as checklists or disguised enumerations.
- **Isolation & Fresh Dispatch**: The main agent is strictly forbidden from reading `references/adversarial_tester.md`. Each round must always spawn a fresh subagent instance; reusing subagent conversations is prohibited.

---

## Governing Principles

### Generality and the action-thought split

A skill steers an agent across two distinct planes with opposite demands: **action** (what the agent executes) and **thought** (how the agent reasons). Confusing the two breaks the skill.

#### Direction of action must be deterministic

Where execution requires exact conformity, eliminate all degrees of freedom. Specify the literal physical contract without variance. Generality in action is workflow entropy.

#### Direction of thought must be general

Steer reasoning exclusively through **generality**.

**Generality** is the extraction of the essential, invariant principle that governs an entire class of problems. It is not vagueness (*"be thorough"* is empty noise). It is the universal common denominator that remains true across every instance without naming any single one.

A general instruction provides a **generative principle**: from one compact definition, the agent deduces every valid variation across any domain or scale.

- **A checklist standing in for a principle is cognitive pollution**: A checklist is an admission that the unifying principle was not found. Listing categories degrades the agent into a clerk ticking boxes, hallucinating relevance for inapplicable items and stopping at the edge of the list instead of reasoning from structure.
- **Detail is sharpness, not count**: When a principle feels too thin to steer, the cure is sharper wording: rewrite it until the cases it must cover become visible inside the words themselves, so the agent meets them while reasoning from the principle. Cases live in authoring (the Scaffolding step of the protocol), where they test the principle; the skill text carries only the principle. A case earns a place in the skill text solely as a boundary clip against a strong pretraining attractor that the principle's wording does not overcome.
- **Examples anchor and blind in the thought plane**: An illustrative instance inside a reasoning directive triggers **exemplar anchoring**: attention collapses onto the surface traits of the sample, mistaking it for the outer boundary of the problem. In the action plane the same move is an **in-line anchor** (see _Constructive contracts_): one example of the output teaches its shape. An anchor uses a situation any reader understands without domain knowledge, so the only traits it carries are the shape being taught.

### Pruning

Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit.

Check every line for **relevance**: does it still bear on what the skill does (not stale or off-topic)?

Then hunt **no-ops** sentence by sentence, not just line by line: run the no-op test (does instruction change behavior versus default?) on each sentence in isolation, and when one fails, delete the whole sentence rather than trim words from it. Be aggressive — most prose that fails should go, not be rewritten.

### Leading words

A **leading word** is a compact concept (_Leitwort_) already living in the model's pretraining that the agent thinks with while running the skill (e.g. _lesson_, _fog of war_, _tracer bullets_). Repeated throughout the text (though not necessarily - a strong leading word might only be needed once), it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens, by recruiting priors the model already holds.

A leading word anchors _execution_: when repeated across prompts, documentation, and skill steps, the agent consistently reaches for the same behavior every time the word appears.

Hunt for opportunities to refactor skills to use leading words. A triad spelled out at three sites (**duplication** — same meaning in more than one place) or verbose explanatory prose is a passage begging to **collapse** into a single token.

### Constructive contracts

Steering by prohibition (**negation**) is a symptom of underspecification: it names what failed without defining the target grammar. Prefer **constructive contracts** that make the desired shape unambiguous:

- **Physical shape over adjectives** — qualitative requests (_"be concise"_) are no-ops. Define the physical contract positively through observable, mechanically verifiable constraints on the output, eliminating all qualitative degrees of freedom.
- **In-line anchors** — in the action plane, a single concrete, realistic example of the output anchors generation density and tone far more reliably than paragraphs of abstract rules. Anchors teach output shape only; reasoning directives stay general (see _Examples anchor and blind_).
- **Boundary repulsion** — use negative guardrails (`Do NOT`) strictly as secondary boundary clips to suppress strong pre-training attractors, never as the primary generator.

### Failure modes

- **Premature completion** — ending a step before it's genuinely done, attention slipping to _being done_. Defence, in order: sharpen the completion criterion first (cheap, local); only if it is irreducibly fuzzy _and_ you observe the rush, hide the post-completion steps by splitting (the sequence cut).
- **Duplication** — the same meaning in more than one place. Costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. Default fate of any skill without a pruning discipline.
- **Sprawl** — a skill simply too long, even when every line is live and unique. Cure: disclose **reference** behind pointers, and split by **branch** or sequence. **Guardrail**: Inline material required by all branches; only put behind a pointer what some branches reach.
- **No-op** — a line the model already obeys by default, so you pay load to say nothing. The test: does it change behaviour versus the default? A weak leading word (_be thorough_ when the agent is already thorough-ish) is a no-op; the fix is a stronger word (_relentless_), not a different technique.
- **Negation** — steering by prohibition backfires: _don't think of an elephant_ makes the elephant more available. Reframe prohibitions into constructive physical contracts; keep negative rules solely as boundary guardrails.
- **Disguised enumeration** — the cosmetic retreat when forbidden from using checklists. Rather than deriving a general principle, the model collapses bulleted items into a comma-separated clause within prose. The underlying structure remains an enumerated checklist, still forcing the agent to audit irrelevant nouns instead of reasoning from structure.
- **Exemplar anchoring** — supplying illustrative instances within reasoning directives. The model anchors on the accidental properties of the example, blinding it to valid architectures outside the example's shadow.
- **Pseudo-generality** — using big words to fake generality. Plain language exposes bad logic immediately; heavy jargon hides it. If an instruction cannot be stated simply, the unifying principle was not found.

---

## Execution Protocol

### 1. Ingestion
Read `<target-skill-path>` with `view_file`. Parse rounds $N$ (default: 10). Initialize `<Artifact Directory>/hardened_<skill_name>.md` with the content of `<target-skill-path>`. Separate Action Direction (physical contracts, steps, formats) from Thought Direction (principles and reasoning).

### 2. Adversarial Loop ($r = 1 \dots N$)
For each round:
1. **Fresh Subagent Spawn**:
   - The main agent is strictly forbidden from reading `references/adversarial_tester.md`.
   - In each round, always spawn a brand new subagent via `invoke_subagent` (never reuse previous subagent conversations):
     - **TypeName**: `self`
     - **Role**: `Adversarial Case Generator`
     - **Prompt**: `Read <skill-dir>/references/adversarial_tester.md. Audit <Artifact Directory>/hardened_<skill_name>.md. List all uncaptured cases for each general principle.`
2. **Convergence Gate**: If the subagent certifies `CONVERGENCE ACHIEVED`, terminate the loop immediately.
3. **Scaffolding to Synthesis**: For each principle with escaping cases:
   - Identify the single underlying structural invariant connecting the existing scope and the new cases.
   - Rewrite the principle so the cases become visible inside the words themselves. Do not add checklists.
   - Verify monotonic generality: the new wording must strictly subsume prior coverage without narrowing.
   - Overwrite `<Artifact Directory>/hardened_<skill_name>.md` with the updated content.
4. **Diff Regeneration**:
   - Regenerate `<Artifact Directory>/<skill_name>_diff.patch` via `diff -u`:
     ```bash
     diff -u "<target-skill-path>" "<Artifact Directory>/hardened_<skill_name>.md" > "<Artifact Directory>/<skill_name>_diff.patch" || true
     ```

### 3. Delivery & Review Gate
1. `<Artifact Directory>/hardened_<skill_name>.md` contains the finalized hardened skill.
2. Generate `<Artifact Directory>/<skill_name>_diff.patch` via `diff -u`:
   ```bash
   diff -u "<target-skill-path>" "<Artifact Directory>/hardened_<skill_name>.md" > "<Artifact Directory>/<skill_name>_diff.patch"
   ```
3. Present the diff to the user with clickable links and request confirmation before applying any overwrite to `<target-skill-path>`.
