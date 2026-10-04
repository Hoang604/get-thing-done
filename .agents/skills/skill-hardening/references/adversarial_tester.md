# Skill Generality Tester

## 1. What a Skill Is

A skill exists to wrangle determinism out of a stochastic system. Its root virtue is **predictability**—the agent taking the same process every run, not producing identical output. A skill steers an agent across two distinct planes:
- **Action (Deterministic)**: Execution requiring exact conformity, eliminating all degrees of freedom.
- **Thought (General)**: Reasoning steered exclusively through generality and generative principles.

## 2. What a Skill Should Be

A skill's thought plane must be **general**: the extraction of the essential, invariant principle that governs an entire class of problems.
- **Generative principle**: From one compact definition, the agent deduces every valid variation across any scale without naming any single one.
- **No checklists (Cognitive pollution)**: A checklist is an admission that the unifying principle was not found. Listing categories degrades the agent into a clerk ticking boxes instead of reasoning from structure.
- **Detail is sharpness, not count**: Cases live in authoring to test the principle; the skill carries only the principle. When a principle feels too thin, the cure is sharper wording until the cases it must cover become visible inside the words themselves.

## 3. Your Task

You are auditing the target skill to discover where its principles are not yet general enough.

For each general principle in the target skill:
- Actively search for and list concrete, real-world engineering cases that the current principle **does not catch**: situations where the current wording provides no guidance, fails to govern, or leaves the agent unable to deduce the correct action from the principle alone.
- Formulate each uncaptured case with its concrete situation and the exact reason the current wording fails to reach it.

If across all principles no uncaptured cases can be found despite thorough analysis, certify: `CONVERGENCE ACHIEVED`.

## Output Contract

For each audited principle:
- **Principle**: `<Exact text of the principle>`
- **Uncaptured Cases**:
  - `<Case: Concrete situation, and why the current principle fails to catch or govern it>`
