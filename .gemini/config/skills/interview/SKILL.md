---
name: interview
description: Interactive alignment interview to build shared understanding before planning or execution
disable-model-invocation: true
---

## Prime Directive

The sole success criterion: you and the user hold the exact same understanding of
what needs to be done before any work begins. Shared understanding is never assumed.
It is proven by a confirmed playback.

## The Continuous Background Thread

Maintain actively throughout execution:

- **Zero Hallucination**: Extract parameters, paths, and facts exclusively from the
  user's explicit text. Map any unprovided file path, data schema, or edge case
  immediately to a `[MISSING]` tag.
- **Semantic Sync**: Identify ambiguous or overloaded domain nouns and verbs. Propose
  a precise **Working Definition** for each and request explicit user confirmation
  to lock the meaning.
- **Blast Radius Rollback**: Halt execution immediately when a newly discovered detail
  conflicts with established context. Output the exact conflict and wait for the user
  to resolve it.
- **Decision Log**: After every question round, append each newly locked answer as one
  bullet under a running `## Decision Log`, echoed in chat. The final playback MUST be
  composed exclusively from this log — never from memory.

## Step 1: Exploration & Legwork

Read the definition of every class, function, and file mentioned in the user prompt.
Inspect BOTH directions of the impact surface: direct dependencies (callees) and
immediate callers of every target symbol, to ground questions in existing conventions
and blast radius. Never ask a question the codebase can answer.
For multi-stage requests, probe in dependency order: resolve upstream stages before
asking dependent technical choices, and record each stage's resolution in the Decision
Log. Never block or defer a question solely because a later stage is unresolved.

## Step 2: Dimension Scan

Before the first question, silently walk all four dimensions. This scan runs on EVERY
invocation regardless of size or clarity:

1. **Scope** — What is being built? What is explicitly excluded?
2. **Acceptance** — How will the user verify the result is correct?
3. **Constraints** — Performance, security, compatibility, migration, deadlines?
4. **Integration** — Which existing conventions, patterns, and modules must this change align with?

Each dimension closes in exactly one way:

- **ASKED**: Load-bearing unknown that code reading cannot resolve — becomes
  question(s) in Step 3.
- **SELF-RESOLVED**: Closed from code evidence or unambiguous convention — becomes
  an Assumption listed verbatim in the Playback.
- **UNRESOLVED**: User cannot know it yet (exploratory/spike work) — marked
  `[UNRESOLVED]` in the Playback with your chosen provisional default.

Strictness lives here, not at the user: think through everything, interrogate only
what is load-bearing.

## Step 3: Relentless Interview

Use the `ask_question` tool to resolve every `[MISSING]`, ASKED dimension, and
Semantic Sync term. Probe in strict dependency order: primary intent and outcome
first, then data and architecture flow, then edge cases and failure recovery, then
scope boundaries.

Questioning rules:

- Pair every question with 2–3 concrete technical choices, plus one pre-calculated `(Recommended)` default listed first. Format options as the user's direct response.
- **Decision-Framed Options**: Format every option as: `<User Action / Technical Choice> — Choose this if <condition>` (e.g., *'if you prefer [X] over [Y]'*, *'if [Z] is the most important thing you care about'*, or *'if <relevant context, constraint, or trade-off holds true>'*).
- Use `is_multi_select: true` when multiple independent choices or constraints can be
  selected simultaneously.
- Batch related questions into few rounds. Maximize signal per interruption.

Assume every user reply is incomplete. Recursively execute Steps 1–2 on each response,
actively hunting for newly introduced unprovided paths, schemas, or edge cases.
Every new tag triggers a new question round.

## Step 4: Playback Gate

When all dimensions and open questions are resolved, switch state header to `[CONSULT-playback]`.

**Strict Text-First Invariant:**
You must NEVER invoke `ask_question` with an empty or truncated chat response. The full `## Shared Understanding` markdown block MUST be generated in the conversational text body of the response BEFORE the confirmation gate.

### Part A: Visible Playback Text (Mandatory Chat Output)
Output the complete synthesized markdown block directly into the chat response, composed strictly from the Decision Log. Never write files:

> ## Shared Understanding
> - **Goal**: <root problem and motivation, one sentence>
> - **User Flow & End-State**: <concrete step-by-step behavior and observable outcome>
> - **In Scope**: <what will be built>
> - **Out of Scope**: <explicit exclusions>
> - **Acceptance Criteria**: <verifiable conditions for "done">
> - **Technical Contracts**: <schema changes, API signatures, state transitions — or "None">
> - **Constraints & NFRs**: <or "None stated">
> - **Codebase Integration**: <files, patterns, modules touched, callers affected>
> - **Edge Cases & Failure Modes**: <exact recovery/error behaviors — or "None identified">
> - **Assumptions**: <every SELF-RESOLVED decision, individually vetoable>
> - **Unresolved**: <each `[UNRESOLVED]` item with its provisional default>

### Part B: Confirmation Gate (`ask_question` Tool)
Accompany the visible text above by invoking `ask_question` with `is_multi_select: true`:
- **Question**: `"Please review the ## Shared Understanding presented above in chat. Which items are wrong or need adjustments?"`
- **Options**:
  - `(Recommended) None — exact`
  - List each individual item from **Assumptions** and **Unresolved** as separate selectable options.

- **None selected / (Recommended) None chosen** — alignment confirmed.
- **Any correction** — convert each corrected item into targeted Step 3 questions,
  produce a revised full playback, and repeat the gate. Loop until exact.

Exit declarations are exclusive:

- All dimensions resolved: declare `[ALIGNED]`.
- Any dimension `[UNRESOLVED]`: declare `[ALIGNED-PROVISIONAL]` — confirmation then
  approves a working direction, not an exact understanding.

After exit: confirm alignment is locked, stop, and wait for the next request.
You must not write any implementation plan or make any code change.

### Sanctioned Skip Override

If the user explicitly instructs to skip ("skip it", "just build"), declare
`[ALIGNED-SKIPPED]` with one line: "Playback offered and declined by user." Then stop
interviewing and proceed per the active execution state. Offer playback once only —
re-offering or further interrogation is forbidden. The agent may suggest skipping
when the task appears trivial, but may never self-trigger this override.

## Postfixes

- `-interview`: When asking specific questions.
- `-playback`: When presenting the Shared Understanding for confirmation.
