---
name: writing-great-skills
description: Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable.
disable-model-invocation: true
---

A skill exists to wrangle determinism out of a stochastic system. **Predictability** — the agent taking the same _process_ every run, not producing the same output — is the root virtue; every lever below serves it.

## Invocation

All skills are user-invoked (`disable-model-invocation: true`). `description` is a human-facing summary.

## Information hierarchy

A skill is built from two content types — **steps** (ordered actions in `SKILL.md`, primary tier) and **reference** (definitions, rules, parameters, or facts consulted on demand, secondary tier) — that mix freely: a skill can be all steps, all reference, or both. The core decision is which to use and where each sits on the **information hierarchy**, a ladder ranked by how immediately the agent needs the material:

1. **In-skill step** — an ordered action in `SKILL.md`, the primary tier: what the agent does, in order. Each step ends on a **completion criterion** (the condition that tells the agent the work is done). Make it _checkable_ (can the agent tell done from not-done?) and, where it matters, _exhaustive_ ("every modified model accounted for", setting high demand) — a vague criterion invites **premature completion** (ending a step before it is genuinely done).
2. **In-skill reference** — a definition, rule, or fact in `SKILL.md`, consulted on demand. Often a legitimately flat peer-set (every rule of a review on one rung) — a fine arrangement, not a smell. _This skill is all reference._
3. **External reference** — plain reference file outside any skill, reached via **context pointer**. Home for shared reference.

A demanding completion criterion drives thorough **legwork** — the behind-the-scenes digging the agent does within the work (reading files, exploring codebase, verifying state) — whether the skill has steps or not, since "every rule applied" binds flat reference just as "every step done" binds a sequence.

Push too little down and the top bloats; push too much and you hide material the agent actually needs. That tension is the whole decision.

**Progressive disclosure** is the move down the ladder — out of `SKILL.md` into a linked file — so the top stays legible. Mechanics: a linked `.md` file in the skill folder, named for what it holds. Some skills are used in more than one way, and each distinct way is a **branch** — different runs taking different paths through the skill. Branching is the cleanest disclosure test: inline what every branch needs, and push behind a pointer what only some branches reach.

Writing a **context pointer**: Wording, not target file, decides reliability. Combine an explicit trigger condition (WHEN), target name (WHAT), and imperative action verb (DO) with shared **leading words** (e.g., "When [condition], read [file] to [goal]"). A missed target behind a weak pointer is a wording bug — sharpen trigger wording before pulling material back inline.

Where the ladder decides _how far down_ a piece sits, **co-location** decides _what sits beside it_ once there: keep a concept's definition, rules, and caveats under one heading rather than scattered, so reading one part brings its neighbours with it.

## When to split

**Granularity** is how finely skills are divided. Splitting user-invoked skills spends **cognitive load** (more skills for the human to remember), so split only when sequence isolation earns it:

- **By sequence** — split a run of **steps** when steps ahead (**post-completion steps**) tempt the agent into **premature completion**, **AND** the earlier step does not need to know the later step's details to make sense.
  - _Can split_: `propose method` and `draft plan` — evaluating technical trade-offs does not require knowing plan document structure.
  - _Cannot split_: `legwork` and `propose method` — legwork needs proposal context (otherwise in a vacuum). Even when the model envisions the proposal early, attention anchors on confirming that outcome, shortcutting investigation into thin legwork.

## Pruning

Keep each meaning in a **single source of truth**: one authoritative place, so changing the behaviour is a one-place edit.

Check every line for **relevance**: does it still bear on what the skill does (not stale or off-topic)?

Then hunt **no-ops** sentence by sentence, not just line by line: run the no-op test (does instruction change behavior versus default?) on each sentence in isolation, and when one fails, delete the whole sentence rather than trim words from it. Be aggressive — most prose that fails should go, not be rewritten.

## Leading words

A **leading word** is a compact concept (_Leitwort_) already living in the model's pretraining that the agent thinks with while running the skill (e.g. _lesson_, _fog of war_, _tracer bullets_). Repeated throughout the text (though not necessarily - a strong leading word might only be needed once), it accumulates a distributed definition and anchors a whole region of behaviour in the fewest tokens, by recruiting priors the model already holds.

A leading word anchors _execution_: when repeated across prompts, documentation, and skill steps, the agent consistently reaches for the same behavior every time the word appears.

Hunt for opportunities to refactor skills to use leading words. A triad spelled out at three sites (**duplication** — same meaning in more than one place) or verbose explanatory prose is a passage begging to **collapse** into a single token. Examples include:

- "fast, deterministic, low-overhead" -> _tight_ — one quality restated across a phase — into a single pretrained word (a _tight_ loop).
- "a loop you believe in" -> _red_ — converts a fuzzy gate into a binary observable state (the loop goes _red_ on the bug, or it doesn't).

You win twice over: fewer tokens, _and_ a sharper hook for the agent to hang its thinking on. Assume every skill is carrying restatements that leading words retire — go find them.

## Failure modes

Use these to diagnose issues the user may be having with the skill.

- **Premature completion** — ending a step before it's genuinely done, attention slipping to _being done_. Defence, in order: sharpen the completion criterion first (cheap, local); only if it is irreducibly fuzzy _and_ you observe the rush, hide the post-completion steps by splitting (the sequence cut).
- **Duplication** — the same meaning in more than one place. Costs maintenance and tokens, and inflates a meaning's prominence on the ladder past its real rank.
- **Sediment** — stale layers that settle because adding feels safe and removing feels risky. Default fate of any skill without a pruning discipline.
- **Sprawl** — a skill simply too long, even when every line is live and unique. Hurts readability and maintainability and wastes tokens. The cure is the ladder: disclose **reference** behind pointers, and split by **branch** or sequence so each path carries only what it needs.
- **No-op** — a line the model already obeys by default, so you pay load to say nothing. The test: does it change behaviour versus the default? A weak leading word (_be thorough_ when the agent is already thorough-ish) is a no-op; the fix is a stronger word (_relentless_), not a different technique.
- **Negation** — steering by prohibition backfires: _don't think of an elephant_ names the elephant and makes it more available, not less. Prompt the **positive** — state the target behaviour so the banned one is never spoken; keep a prohibition only as a hard guardrail you can't phrase positively, and even then pair it with what to do instead.
