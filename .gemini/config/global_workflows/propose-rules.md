---
name: propose-rules
description: Analyze agent trajectory or codebase artifacts for decision flaws and propose global rule improvements without editing files.
disable-model-invocation: true
---

## Core Principles & Leading Words

- **Decision Point**: Either the exact turn/action where the agent erred in the current conversation (`Active Trajectory`), or the specific code anti-pattern/defect observed in the codebase (`Code Inspection`).
- **Pattern Defect**: A concrete code anti-pattern, architectural flaw, or missing defense observed during codebase inspection, serving as undeniable mechanical proof of a rule gap.
- **Root Flaw**: The underlying systemic gap in assumptions, verification, or defensive practices (`<RULE[user_global]>`) that caused the divergence at the `Decision Point` or allowed the `Pattern Defect` to be generated.
- **Global Principle**: A universal invariant rule devoid of local context (no specific file paths, variable names, or project-specific architecture).

---

## Target Blocks

All proposals must strictly target one of these four sections in `<RULE[user_global]>`:

1. `# Intent Classification & Execution Model` (Rules governing state classification [CONSULT] vs [MUTATE_WORKFLOW], phase transitions CONFIRM -> EXECUTE, exploration, confirmation, and failure handling)
2. `# Context & Tool Mechanics` (Rules governing tool selection, batching, reads, edits, and context management)
3. `# Anti-Hallucination & Verification` (Rules governing mechanical proof, API verification, logic verification, and tracing)
4. `# Code Quality Defenses` (Rules governing defensive coding, I/O performance, concurrency, state management, and error handling)

---

## Workflow

### Step 1: Retrospective & Decision Point Analysis

Inspect the current conversation trajectory or codebase artifacts.

1. **Identify the Trigger**:
   - **Active Trajectory Branch**: Trace where errors, missteps, or user corrections occurred during the current conversation.
   - **Code Inspection Branch**: Isolate exact code anti-patterns (`Pattern Defect`), structural flaws, or missing defenses observed in codebase files from past sessions.
2. **Isolate the Decision Point**: Pinpoint the exact turn of divergence (`Active Trajectory`) or the specific code structure exhibiting the defect (`Code Inspection`).
3. **Determine the Root Flaw**: Why did existing system instructions (`<RULE[user_global]>`) and priors allow this failure or permit this code structure to be written? (For `Code Inspection`, do not guess or reconstruct past thoughts outside context; treat the code artifact itself as mechanical proof of a rule gap).

_Completion Criterion_: Every identified mistake, correction, or code defect in scope is mapped to exactly one `Decision Point` (`Active Trajectory` or `Code Inspection`) and its underlying `Root Flaw`.

---

### Step 2: Global Rule Synthesis & Pruning

Formulate candidate rule additions or modifications for the exact target block that governs the `Root Flaw`. Apply these strict filters to every candidate rule before finalizing:

1. **Global Principle Check**: Strip all local references. If the rule mentions a specific file, class, function, or project pattern, rewrite it until it applies universally across any repository.
2. **No-Op Test**: Will this rule change agent behavior compared to default model behavior? If the model already follows the rule by default, discard it.
3. **Single Source of Truth Check (`[ADDITION]` vs `[MODIFICATION]`)**:
   - **When to Modify (`[MODIFICATION]`)**: If any existing bullet in `<RULE[user_global]>` touches the same domain, concept, or tool mechanic, you **MUST** propose a `[MODIFICATION]` to refine, clarify, or split that existing rule. Never append a new rule just because adding feels safe; adding to an existing domain creates **Duplication** and **Sediment** (`writing-great-skills`).
   - **When to Add (`[ADDITION]`)**: Propose an `[ADDITION]` **ONLY** when the `Root Flaw` exposes a completely new domain, vulnerability class, or behavioral pattern that is 100% absent across the entire target block.
4. **Positive Framing**: State the required action ("Do X before Y") instead of a bare prohibition ("Never do Z"), unless the prohibition is a hard safety guardrail.

_Completion Criterion_: A deduplicated, pruned list of universal rule changes or additions sorted by their target block.

---

### Step 3: Proposal Presentation (Terminal Step)

Present the final proposals clearly to the user using the format below. **For each proposal, you MUST wrap only the `Proposed Text` inside a fenced `markdown` code block without leading blockquotes (`>`) so the user can copy just the rule text cleanly.** **Stop execution immediately after outputting the report.**

#### Proposal Report Format

# Rule Proposals

## 1. Target Block: <Exact Block Name>

### Proposal A: <Short Title>

- **Type**: `[ADDITION]` or `[MODIFICATION of existing rule]`
- **Branch**: `[Active Trajectory]` or `[Code Inspection]`
- **Decision Point**: <Exact turn/action where agent erred, or exact code structure/Pattern Defect observed>
- **Root Flaw**: <Why the existing priors or <RULE[user_global]> failed to prevent this>
- **Proposed Text**:

```markdown
- **<Rule Title>**: <Exact proposed bullet point or modification>
```

_Completion Criterion_: All pruned proposals rendered with only their `Proposed Text` inside fenced `markdown` code blocks in chat. Execution halted without mutating anything.
