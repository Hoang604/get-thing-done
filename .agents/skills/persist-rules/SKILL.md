---
name: persist-rules
description: Extract recurring decisions from the session and synthesize rules into the repository's GEMINI.md or AGENTS.md
disable-model-invocation: true
---

A repository system prompt (`GEMINI.md` or `AGENTS.md`) conditions every turn in the workspace before the agent reads task-specific code. Its value comes from governing decisions where the model's default fails and where the code a task touches does not already force the answer, while spending attention only when each governed decision arises.

## What to Persist

Every candidate to persist is an independent decision where the agent's default acts against the user's or repository's requirement and whose answer is not already forced by reading the code slice a task touches. Strip away task-local state and summaries of what the code already says in the files a run must read anyway, isolating the underlying decision, the observable moment it arises, and the required outcome to present to the user in Step 1.

## Instruction Synthesis

Begin every rule with **When** and the condition the agent can observe at the moment it must act, and state the goal—the exact state or action to produce—so the agent can verify its own work against it before acting.
- **When** the judge fixes the valid choices (a **Closed** question), write a literal contract naming those exact choices and leaving no room for interpretation.
- **When** the rule governs unseen situations (an **Open** question), state in one sentence the cause that makes the right action right across all observed and held-out cases and rules out every tempting wrong action, without listing individual cases or hiding behind abstract degree words.
Place a prohibition (`Never...` / `Tuyệt đối không...`) only as a guardrail immediately after the positive goal it protects, naming the specific default habit the agent would otherwise rationalize as compliant.

## Integration and Pruning

Read the entire target file before drafting so every question is answered in exactly one place under one heading. **When** an existing section already governs the same question or shares the same cause, re-synthesize the existing passage and the new requirement into a single general instruction and delete every sentence in that section that the update supersedes (**sediment**), repeats (**duplication**), conflicts with (**contradiction**), or that states what the agent already does by default (**no-op**). **When** no existing section governs the question, add a new heading for it. Leave unrelated sections untouched.

## Execution Protocol

1. **Resolve the target file and settle what to persist**:
   - Check the repository for `GEMINI.md` and `AGENTS.md`. Update whichever single file exists (`GEMINI.md` when neither exists yet). **When** both `GEMINI.md` and `AGENTS.md` exist in the repository, report both paths immediately and ask the user via `ask_question` to choose the single target file.
   - Read the target file in full and apply *What to Persist* to the current conversation and user request. Present to the user the exact decision(s) identified to persist, their classification as **Closed** or **Open**, and which existing section of the target file each decision updates (or that it forms a new section). **When** any candidate decision, its scope, or its right action lacks an explicit ruling from the user or a cited repository source, call `ask_question` with concrete scenarios and competing options so the user settles it.
   *Completion criterion*: a single target file (`GEMINI.md` or `AGENTS.md`) is identified and read in full, the exact decision(s) to persist have been presented to the user, and every question has a quoted ruling from its judge; if `ask_question` was called, the turn ends to await the user's answer before Step 2 runs.

2. **Synthesize, verify, and write**:
   - **When** every decision to persist is **Closed** with a settled ruling from its judge: synthesize the literal contract under *Instruction Synthesis* and *Integration and Pruning* and write the update directly to the single target file.
   - **When** any decision to persist is **Open**: output to the conversation for each **Open** decision:
     - **Scaffolding**: the observed cases from the session and the existing target file, each with its concrete situation, the judge-ratified right action, and the tempting wrong actions.
     - **Synthesis**: the exact rule text produced under *Instruction Synthesis* and *Integration and Pruning*, in the language of the target file.
     - **Fit test**: verification of that **Synthesis** alone against every case in *Scaffolding*.
     - **Held-out case**: one concrete scenario outside *Scaffolding* with competing options, stating which option **Synthesis** alone picks.
     **When** the user rejects the chosen option, add that held-out case to *Scaffolding* with the user's choice as the right action and the rejected choice as a tempting wrong action, and repeat Step 2 with a revised **Synthesis** and a new **Held-out case**. **When** the user agrees with the chosen option for every **Open** decision, write the ratified **Synthesis** into the single target file.
   *Completion criterion*: for every **Open** decision, the user has agreed with the option **Synthesis** picks on its held-out case, and the single target file (`GEMINI.md` or `AGENTS.md`) is updated on disk with the ratified instruction(s) and all superseded, duplicate, conflicting, or no-op sentences in the touched section(s) removed.
