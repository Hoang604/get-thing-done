---
name: interview
description: Interview to align understanding
disable-model-invocation: true
---

## The Continuous Background Thread

Maintain these processes actively throughout the execution:

- **Zero Hallucination**: Extract parameters, paths, and facts exclusively from the user's explicit text. Map any unprovided file path, data schema, or edge case immediately to a `[MISSING]` tag.
- **Semantic Sync**: Identify ambiguous or overloaded domain nouns and verbs. Propose a precise **Working Definition** for each and request explicit user confirmation to lock the meaning.
- **Blast Radius Rollback**: Halt execution immediately when a newly discovered detail conflicts with established context. Output the exact conflict and wait for the user to resolve it.

## Step 1: Exploration & Legwork

Read definition of every class, function, and file mentioned in user prompt. Read direct dependencies of target file before ask question.
If the request contains multiple stages, evaluate each independently. Declare `[MISSING_INTENT: <stage>]` or `[MISSING_EXECUTION_PATH: <stage>]`. If a stage's technical choices depend on an unresolved earlier stage, declare `[BLOCKED_EXECUTION_PATH: <stage>]`.

## Step 2: Relentless Interview

Output a numbered list of questions to resolve every `[MISSING]`, `[MISSING_INTENT]`, and `[MISSING_EXECUTION_PATH]` tag. If `[MISSING_EXECUTION_PATH]` exists, present the valid technical choices as A/B options to lock down a singular path. Never present A/B options for a `[BLOCKED_EXECUTION_PATH]`. You must resolve its dependencies first.

**Binary Interrogation**: Formulate every question as a strict verification. Pair every question with a synthesized recommendation or pre-calculated default. State your assumption explicitly to shift the cognitive load; allow the user to answer with a simple "Yes/No" or "A/B" choice.

Stop and wait for the user to answer the list. Assume every user reply is incomplete. You MUST recursively execute Step 1 on the user's new text to actively hunt for newly introduced unprovided paths, schemas, or edge cases. Output a new numbered list for every new `[MISSING]` tag found.
You may only exit this loop when you explicitly declare `[ZERO_NEW_MISSING]`, proving no new variables exist. Your exclusive next action is to confirm to user there is nothing left to ask. Stop and wait for their next request.

## Postfixes

- `-interview`: When asking specific questions.
