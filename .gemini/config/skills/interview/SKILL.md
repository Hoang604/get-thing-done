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

- Pair every question with 2–3 concrete choices, plus one pre-calculated `(Recommended)` default listed first. Format options as the user's direct response.
- **Decision-Framed Options**: Format every option as: `<User Action / Technical Choice> — Choose this if <condition>` (e.g., *'if you prefer [X] over [Y]'*, *'if [Z] is the most important thing you care about'*, or *'if <relevant context, constraint, or trade-off holds true>'*).
- **Pacing Discipline (Fork vs. Leaf)**:
  - **Sequential Rounds (Fork)**: When an upstream choice alters what downstream questions make sense, isolate the fork into its own round. Let the user's answer prune the decision tree before probing downstream details.
  - **Single Round (Leaf)**: When questions are orthogonal, resolve all independent parameters together in a single crisp round.
- Use `is_multi_select: true` when multiple independent choices or constraints can be
  selected simultaneously.

Assume every user reply is incomplete. Recursively execute Steps 1–2 on each response,
actively hunting for newly introduced unprovided paths, schemas, or edge cases.
Every new tag triggers a new question round.

## Step 4: Multi-Tab Playback Gate

When all dimensions are resolved, switch state header to `[CONSULT-playback]`.

Invoke `ask_question` with 4 self-contained tabs (`questions: [...]`). Format each tab strictly using the markdown anchors below:

1. **Goal & Flow** (`is_multi_select: false`):
   - `question`: "### 1. Goal & Observable Flow\n- **Goal**: <1-2 sentences>\n- **User Flow**: <step-by-step actions and outcomes>\n\nIs the goal and flow accurate?"
   - `options`: `["(Recommended) Confirmed — exact goal and user flow", "Goal or user flow needs adjustment"]`
2. **Scope & Acceptance** (`is_multi_select: false`):
   - `question`: "### 2. Scope & Acceptance\n- **In Scope**: <features to build>\n- **Out of Scope**: <deferred/excluded>\n- **Acceptance Criteria**: <verifiable conditions>\n- **Constraints**: <performance/security/none>\n\nAre scope and acceptance correct?"
   - `options`: `["(Recommended) Confirmed — scope and acceptance are solid", "Scope or acceptance needs revision"]`
3. **Technical Contracts** (`is_multi_select: false`):
   - `question`: "### 3. Technical Contracts\n- **Files Touched**: <exact paths>\n- **API / Schema Changes**: <signatures or None>\n- **Callers & Blast Radius**: <affected modules>\n\nDoes the technical design match?"
   - `options`: `["(Recommended) Confirmed — technical contracts are correct", "Technical contracts need changes"]`
4. **Assumptions & Edge Cases** (`is_multi_select: true`):
   - `question`: "### 4. Assumptions & Edge Cases\n- **Assumption 1**: <first assumption>\n- **Assumption 2**: <second assumption>\n- **Edge Cases**: <error/recovery behaviors>\n\nWhich items need adjustment?"
   - `options`: `["(Recommended) None — all assumptions confirmed", "Veto Assumption 1", "Veto Assumption 2"]`

### Correction Loop
- **Any Tab Flagged / Assumption Vetoed**: Re-probe only the disputed dimension via Step 3, then re-issue the gate. Loop until exact.

### Exit & Hand-off
When confirmed, output the template below and halt. Do not re-summarize or mutate code.

**Template (`[ALIGNED]` or `[ALIGNED-PROVISIONAL]`):**
> **[ALIGNED]** — Shared understanding locked.
>
> To evaluate architectural trade-offs before planning, run `/propose-plan` to compare two viable technical approaches (Pragmatic vs. Robust) with Quality Tier analysis.

*(Use `[ALIGNED-PROVISIONAL]` if provisional defaults remain).*

### Skip Override
If user instructs to skip ("skip it", "just build"), output `[ALIGNED-SKIPPED] — Playback offered and declined by user.` and proceed. Offer once only.

## Postfixes
- `-interview`: Asking specific questions.
- `-playback`: Presenting the Multi-Tab Playback Gate.
