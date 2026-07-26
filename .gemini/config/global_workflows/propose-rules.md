---
name: propose-rules
description: Analyze agent trajectory or codebase artifacts for decision flaws and propose global or project-scoped rule improvements without editing files.
disable-model-invocation: true
---

## Core Principles & Leading Words

- **Decision Point**: Either the exact turn/action where the agent erred in the current conversation (`Active Trajectory`), or the specific code anti-pattern/defect observed in the codebase (`Code Inspection`).
- **Pattern Defect**: A concrete code anti-pattern, architectural flaw, or missing defense observed during codebase inspection, serving as undeniable mechanical proof of a rule gap.
- **Root Flaw**: The underlying systemic gap in assumptions, verification, or defensive practices (`<RULE[user_global]>` or `<RULE[AGENTS.md]>`) that caused the divergence at the `Decision Point` or allowed the `Pattern Defect` to be generated.
- **Global Scope (`<RULE[user_global]>`)**: Universal Computer Science invariants devoid of local context, valid across any programming language, framework, or repository structure.
- **Project Scope (`<RULE[AGENTS.md]>` or `<RULE[GEMINI.md]>`)**: Repository-specific architectural conventions, layering rules, framework patterns, and library guardrails that apply across the entire target codebase.

---

## Target Blocks & Scope Categories

All proposals must strictly target one of two scopes and a concrete block within that scope:

### Tier 1: Global Scope (`<RULE[user_global]>`)
Strictly for universal Computer Science invariants passing the **Two-Stack Test**. Target one of these four blocks:
1. `# Intent Classification & Execution Model`
2. `# Context & Tool Mechanics`
3. `# Anti-Hallucination & Verification`
4. `# Code Quality Defenses`

### Tier 2: Project Scope (`<RULE[AGENTS.md]>` or `<RULE[GEMINI.md]>`)
For stack-specific architectural boundaries, ORM patterns, and testing conventions. Target exact project sections (`e.g., # Architecture & Layering, # Database & ORM Conventions, # Testing Framework Rules, # API Standards`).

---

## Workflow

### Step 1: Retrospective & Decision Point Analysis

Inspect the current conversation trajectory or codebase artifacts.

1. **Identify the Trigger**:
   - **Active Trajectory Branch**: Trace where errors, missteps, or user corrections occurred during the current conversation.
   - **Code Inspection Branch**: Isolate exact code anti-patterns (`Pattern Defect`), structural flaws, or missing defenses observed in codebase files from past sessions.
2. **Isolate the Decision Point**: Pinpoint the exact turn of divergence (`Active Trajectory`) or the specific code structure exhibiting the defect (`Code Inspection`).
3. **Determine the Root Flaw**: Why did existing system instructions (`<RULE[user_global]>` or `<RULE[AGENTS.md]>`) allow this failure or permit this code structure to be written? (For `Code Inspection`, treat the code artifact itself as mechanical proof of a rule gap without speculating outside context).

_Completion Criterion_: Every identified mistake, correction, or code defect in scope is mapped to exactly one `Decision Point` (`Active Trajectory` or `Code Inspection`) and its underlying `Root Flaw`.

---

### Step 2: Scope Allocation, Generalization & Pruning

Formulate candidate rule additions or modifications. Apply this strict 2-stage allocation and pruning gate:

1. **Scope Allocation Gate (`Global vs Project Router`)**:
   - **Test 1: Two-Stack De-localization Test (`Global Proof Gate`)**: Does the candidate rule apply with zero modification across at least two radically different technology stacks (`e.g., Python/Postgres backend AND Rust/Embedded system OR TypeScript/Vanilla JS frontend`)?
     - `YES` -> Allocate to **Global Scope (`<RULE[user_global]>`)**. Strip every trace of framework/library names.
     - `NO` -> Allocate to **Project Scope (`<RULE[AGENTS.md]>` or `<RULE[GEMINI.md]>`)**. Proceed to Test 2.
   - **Test 2: Project Generalization Test (`No 1-File Rules`)**: Does the Project-Scoped rule apply universally to *every* component sharing that architectural role across the workspace (`e.g., all controllers, all repository classes, all async tasks`)? If the rule only names a single specific file or function (`e.g., OrderService.py`), **it fails and must be rewritten to cover the entire architectural layer or component family**.
2. **No-Op Test**: Will this rule change agent behavior compared to default model behavior? If the model already follows the rule by default, discard it.
3. **Single Source of Truth Check (`[ADDITION]` vs `[MODIFICATION]`)**:
   - **When to Modify (`[MODIFICATION]`)**: If any existing bullet in the target scope touches the same domain or mechanic, you **MUST** propose a `[MODIFICATION]` to refine or split that existing rule. Keep the rule set deduplicated by modifying the existing rule (`Duplication / Sediment`).
   - **When to Add (`[ADDITION]`)**: Propose an `[ADDITION]` **ONLY** when the `Root Flaw` exposes a completely new domain or architectural pattern 100% absent in that scope.
4. **Positive Framing**: State the required action ("Do X before Y") instead of a bare prohibition ("Never do Z"), unless the prohibition is a hard safety guardrail.
5. **Leading Words**: Collapse fuzzy rule descriptions into strong, compact pretrained words. Anchor the rule's core concept in a specific vocabulary token rather than a rambling sentence.
6. **Completion Criterion**: If the proposed rule dictates an action sequence or process, it must define a hard, checkable end-state to defend against premature completion.
7. **Co-location & Sprawl**: Strictly compress the token count of the rule text. When proposing the rule, ensure its exact placement is adjacent to related concepts within the target block to maintain information hierarchy.

_Completion Criterion_: Before proceeding to Step 3, you must output a 3-column verification table proving scope allocation and generalization for every candidate:

| Local Defect / Trajectory Error | Allocated Scope (`Global vs Project`) | Generalized Rule Text (`Passed Two-Stack or Project Generalization Test`) |
| :--- | :--- | :--- |
| `Leaking uncommitted DB state across loop yield points` | `Global (<RULE[user_global]>)` | Wrap external resource mutations (`disk, storage, network state`) inside explicit context managers or atomic check-then-act boundaries. Contain all state mutations entirely within these boundaries before any I/O yield points or failure paths. |
| `Forgot SQLAlchemy .with_for_update() in OrderService debit` | `Project (<RULE[AGENTS.md]>)` | Always hold explicit row-level database locks (`SELECT ... FOR UPDATE` via `with_for_update()`) inside service layer transaction boundaries before executing read-then-write balance mutations across any financial entity. |
| `Hardcoded raw SQL inside FastAPI controller route handler` | `Project (<RULE[AGENTS.md]>)` | Strictly isolate all SQL and ORM queries inside repository layer classes (`src/repositories/`). Route handlers and serialization logic must exclusively call repository methods to fetch or mutate data. |

Only rules listed in the right column are permitted to enter Step 3 (`Proposal Presentation`).

---

### Step 3: Proposal Presentation (Terminal Step)

Present the final proposals clearly to the user using the format below. **For each proposal, you MUST wrap only the `Proposed Text` inside a fenced `markdown` code block without leading blockquotes (`>`) so the user can copy just the rule text cleanly.** **Stop execution immediately after outputting the report.**

#### Proposal Report Format

# Rule Proposals

## Scope: `[Global (<RULE[user_global]>)]` OR `[Project (<RULE[AGENTS.md]> / <RULE[GEMINI.md]>)]`

### Target Block: <Exact Block Name>

#### Proposal A: <Short Title>

- **Type**: `[ADDITION]` or `[MODIFICATION of existing rule]`
- **Branch**: `[Active Trajectory]` or `[Code Inspection]`
- **Decision Point**: <Exact turn/action where agent erred, or exact code structure/Pattern Defect observed>
- **Root Flaw**: <Why the existing priors or target rules failed to prevent this>
- **Proposed Text**:

```markdown
- **<Rule Title>**: <Exact proposed bullet point or modification>
```

_Completion Criterion_: All pruned proposals rendered with only their `Proposed Text` inside fenced `markdown` code blocks in chat. Execution halted without mutating anything.
