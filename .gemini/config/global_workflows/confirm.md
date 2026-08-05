---
name: confirm
description: Relentless interview to rigorously synchronize language, context, and system topology from top to bottom before execution.
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

Stop and wait for user reply.

## Step 3: Alignment Contract

Advance to Step 3 only when exactly 0 `[MISSING]` tags, 0 `[MISSING_INTENT]`, 0 `[MISSING_EXECUTION_PATH]`, 0 `[BLOCKED_EXECUTION_PATH]`, and 0 unconfirmed Working Definitions remain. Halt and repeat Step 2 if any tags persist.

Output a single unified bulleted contract explicitly stating exactly 4 checkable elements:

1. Exact user's problem/intent.
2. Targets summary: `Targets: <concrete action description> [basenameA](file:///path/basenameA)\n<concrete action description> [basenameB](file:///path/basenameB),...`
3. Deterministic technical choices (locked data models, exact parameters, must be singular execution path).
4. Invariants, out of scope.
5. **Quality Defenses**: Evaluate all 8 mechanisms against the contract. For each mechanism, either declare 'N/A' or output: `- **[Mechanism Name]**: [How it shapes the execution]`:
   - **APIs & Methods**: When calling an API, read the target class/struct definition to verify exact signature and attributes before writing the call.
   - **Dependencies**: When importing a module, read package/dependency config files to verify library exists.
   - **Data & I/O Performance**: When writing loops, batch DB/network calls before the loop. When inside an async context, use async equivalents for all I/O. When fetching data, paginate access or yield lazily via generators. When calculating numerical data, use vectorized operations or slices.
   - **Concurrency**: When writing check-then-act sequences, wrap state mutations in atomic operations or synchronization primitives (`mutexes`, `rwlocks`, `asyncio.Lock`, DB `SELECT ... FOR UPDATE`, distributed `Redis` locks). When holding a lock, extract all DB queries, network calls, and I/O outside the lock boundary. Hold locks only for fast, in-memory state mutations.
   - **State & Resources**: When transforming data, return the new state as a direct output to keep functions pure.
   - **Error Handling & Types**: When handling exceptions, catch specific typed exceptions and throw specific error classes. When state corrupts, crash the process explicitly to fail fast. When accessing nullable variables, validate the null state before access. Enforce strict type hints on all signatures.
   - **Architecture**: When hardcoding magic numbers or configuration strings, extract them to constants or environment variables.
   - **Testing**: When writing tests, assert against external observable outputs. When faking dependencies, mock only external system boundaries (disk/network). Use real objects for all internal logic.

At the end of the contract, output this prompt (adapt to user language): "Please review the contract. Request modification if needed. `/execute` to immediately execute, `/draft-plan` to draft zero entropy implementation plan."

## Postfixes

- `-interview`: When asking specific questions.
- `-confirm`: When outputting alignment contract.
