---
name: spawn-subagent
description: Guide spawning and delegating work to subagents with true autonomy, high-level objectives, adversarial posture, and silent artifact hand-offs
disable-model-invocation: true
---

A subagent operates in an isolated context window with zero pre-existing knowledge of your conversation history, working memory, or thought process (The Amnesia Invariant). By default, LLM subagents are deferential: if told what the parent agent built or concluded, they bias toward confirmation and rubber-stamping.

Delegating effectively requires compiling a **Hermetically Self-Contained Briefing**: resolve all conversational context, define the objective without synthetic constraints, grant an explicit **Operational Posture (The Mandate)**, and enforce silent artifact hand-offs.

---

## The Hermetic Delegation Invariant (The Self-Sufficiency Test)

> **The Self-Sufficiency Test**: A subagent prompt is valid *if and only if* an independent engineer reading **only** that prompt—with zero access to the parent chat history, internal thoughts, or git log—can execute the task unambiguously without having to ask: *"Which hypothesis?"*, *"Which bug?"*, *"Which design?"*, or *"Which component?"*.

Whenever preparing a delegation prompt, pass it through this 3-step compilation pipeline:

1. **Strip Meta-Commands**: Filter out parent-orchestration tokens (*"use spawn-subagent to..."*, *"delegate this to an agent..."*, *"call subagent..."*). Extract only the core engineering directive.
2. **De-Reference & Materialize Context (The Anti-Amnesia Rule)**:
   - Identify every conversational pronoun, relative reference, or implicit concept (*"this hypothesis"*, *"that error"*, *"approach A"*, *"the code we just modified"*, *"this PR"*).
   - Fully expand and materialize each reference into an explicit, objective technical summary in `Delegated Subject` (the exact hypothesis mechanics, observed symptoms, or architectural trade-offs under debate).
3. **Preserve Authentic User Intent (No Synthetic Constraints)**:
   - State the user's authentic standard of truth and success criteria.
   - Never invent arbitrary constraints, speculative frameworks, or artificial acceptance criteria that the user did not specify.

---

## Delegation Workflow (What to Do First)

Follow this sequence whenever preparing and dispatching an `invoke_subagent` call:

### 1. Ground Context & Materialize the Subject
Supply upstream context to satisfy the Self-Sufficiency Test. Omit optional/conditional sections if inapplicable—never include empty headers:
- **[REQUIRED] Domain Context / Problem State**: The overarching subsystem, feature domain, or investigation area.
- **[REQUIRED] Delegated Subject**: The concrete hypothesis, proposal, design, subsystem, or target behavior—fully materialized with zero conversational pronouns.
- **[REQUIRED] Authentic User Intent**: What the user genuinely asked to achieve or verify, stripped of orchestration meta-words and free of synthetic constraints.
- **[CONDITIONAL] Business Context / Ground Truth**: Core domain policies and rules defining correctness independent of code. Required when auditing business logic so the subagent does not mistake pre-existing bugs for intended behavior. Omit for purely technical or infrastructure tasks (e.g. build scripts, AST parsing).
- **[OPTIONAL] Operational / Runtime Context**: Execution model reality (concurrency, async flows, actors, workload conditions). Omit if execution is synchronous or pure logic.
- **[OPTIONAL] Architectural Invariants**: Specific architectural boundaries or stack patterns governing the task. Omit if no special invariants apply.

### 2. Define the Primary Objective [ALWAYS REQUIRED]
Specify the concrete deliverable and outcome, not the procedural path:
- **Outcome-Only Focus**: Define the target behavioral state to verify (audit alignment against user intent, identify unintended side effects).
- **The Amnesia Gate (Zero Commit History)**: Treat recent code edits as non-existent to the subagent. Frame objectives against the steady-state contract, never git diff history.
- **The Zero-`e.g.` Ban**: The tokens `e.g.`, `such as`, or `like` are strictly forbidden. Examples cause anchoring bias; force the subagent to discover the complete domain independently.
- **Discovery Freedom**: Never spoon-feed file paths, function names, or line numbers. Let the subagent locate files, trace dependencies, and evaluate solutions independently.

### 3. Grant the Operational Posture (The Mandate) [CONDITIONAL]
Separate *what to do* (the objective) from *the lens and authority to do it* (the posture):
- **Audit / Review / Verification / Debugging [REQUIRED]**: Subagents naturally suffer from confirmation bias and rubber-stamping. Grant an explicit mandate:
  - **The License to Doubt (Zero-Trust Stance)**: Authorize treating existing implementations and hypotheses as unverified assumptions.
  - **Epistemic Independence**: Frame the persona as an external or adversarial engineer who owes no loyalty to prior decisions.
  - **First-Principles Auditing**: Require independent deduction of boundary conditions without pre-supplied checklists.
- **Builder / Generator [ADAPTABLE]**: For generative, refactoring, or implementation tasks, replace adversarial posture with role-appropriate execution mandates.

### 4. Enforce Silent Artifact Transfer (`cp` / `mv`) [CONDITIONAL]
Prevent deep reviews, audits, and matrices from flooding the parent conversation:
- **When Applicable [REQUIRED for write-capable agents e.g. `self`]**:
  - Subagent creates artifacts within its sandbox (`<appDataDir>/brain/<subagent-id>/<artifact_name>.md`).
  - Subagent copies the completed artifact into the parent directory via bash:
    `cp "<appDataDir>/brain/<subagent-id>/<artifact_name>.md" "<parent-conversation-dir>/<artifact_name>.md"`
  - Subagent returns **strictly a single status line** in chat confirming completion. Chat leakage/summaries are forbidden.
  - Parent agent ingests the artifact directly via `view_file`.
- **When Not Applicable [OMIT]**: For read-only subagents (e.g. `research`) without bash tools, or tasks returning concise scalar answers directly in chat.

### 5. Model Selection
Always prefer `inherit` model even for researching tasks.

---

## Prompt Construction Blueprint

Assemble the `Prompt` argument for `invoke_subagent` using this 4-part structure. Prune optional/conditional fields when not applicable—never emit empty headers or "N/A":

```markdown
### 1. Context & Delegated Subject (Hermetically Self-Contained)
- Domain Context: <REQUIRED: Overarching problem, feature, or investigation background>
- Delegated Subject: <REQUIRED: Concrete hypothesis, proposal, design, or target behavior—materialized with zero pronouns>
- Authentic User Intent: <REQUIRED: Real outcome the user wants verified or generated, free of synthetic constraints>
- Business Context / Ground Truth: <CONDITIONAL: Core business rules defining correctness; omit for purely technical/infra tasks>
- Operational Context: <OPTIONAL: Concurrency, async flows, or scale reality; omit if single-threaded/synchronous>
- Architectural Invariants: <OPTIONAL: Known architectural boundaries or conventions; omit if standard>

### 2. Primary Objective [ALWAYS REQUIRED]
<Outcome-only objective statement. Zero 'e.g.' examples. Zero named entity/file paths. Zero references to your recent code edits.>

### 3. Operational Posture (The Mandate) [CONDITIONAL: Required for Audit/Verification/Review]
- Persona: External, third-party auditor who has never seen this codebase.
- Zero-Trust Baseline: Treat all existing implementations, hypotheses, and recent changes as unverified assumptions. Do not assume any code is complete, correct, or located in the right layer.
- First-Principles Deduction: Deduce all domain edge cases, failure states, and boundary conditions independently from first principles. Do not rely on pre-supplied checklists.
<!-- For builder/generation subagents, replace with role-appropriate constructive mandate -->

### 4. Delivery Protocol [CONDITIONAL: Required for write-capable agents with large deliverables]
1. Write your full, exhaustive findings to an artifact named `<artifact_name>.md`.
2. Copy the artifact into my conversation folder using bash:
   cp "<appDataDir>/brain/<subagent-id>/<artifact_name>.md" "<parent-conversation-dir>/<artifact_name>.md"
3. In your final chat reply, provide ONLY this single confirmation line (do NOT summarize or leak artifact content in chat):
   "Completed: Report written and copied to <artifact_name>.md"
<!-- For read-only subagents or lightweight tasks, instruct returning results directly in chat -->
```

---

## Delegation Contrast: The 3 Levels of Prompting

- ❌ **Level 0: Blatant Micromanagement (Obvious Failure)**
  > *"I added the auth logic in `src/auth/service.ts`. Read lines 35–70 to check if `validateToken` exists."*  
  *(Fails obviously: Treats the subagent as a mechanical code-reader confirming facts the parent already knows).*

- ⚠️ **Level 1: The False-Elevation Trap (Insidious Failure / "Thought it was a success")**
  > *"Verify whether `validateToken` in `src/auth/service.ts` correctly handles expired tokens and satisfies user requirements."*  
  *(Why the parent agent thinks it succeeded: It used outcome verbs like 'verify' and cited 'handles edge cases' and 'satisfies requirements').*  
  *(Why it actually fails: It pre-selects the file and function name, and pre-barks the exact edge case the parent already handled. The subagent evaluates that single function against that single case, confirms it works, and misses that the function is never wired into the router or that broader concurrency bugs exist. The parent's blind spot becomes the subagent's blind spot).*

- ✅ **Level 2: Hermetic Autonomous Delegation (Self-Contained + Posture + Silent Transfer)**
  > *"You are an external systems auditor who has never seen this codebase.*  
  >*Domain Context: User authentication and token lifecycle under high concurrency.*  
  >*Delegated Subject: The working hypothesis that token revocation events are dropped when Redis reconnects during network partition.*  
  >*Authentic User Intent: Independently evaluate whether this failure mode is structurally possible and identify alternative root causes or unhandled race conditions.*  
  >*Operate under a zero-trust posture: treat all existing implementations and hypotheses as unverified assumptions, trace dependencies with fresh eyes, and deduce boundary conditions from first principles without pre-supplied checklists.*  
  >*Write your complete audit report to an artifact `<artifact_name>.md`, copy it to `<parent-conversation-dir>/<artifact_name>.md`, and reply with only a single confirmation line."*

---

## Failure Modes to Avoid

### 1. Deictic Amnesia & Verbatim Parroting (The Conversational Trap)
- **What happens**: The parent agent parrots the user's conversational prompt verbatim when it contains relative references or pronouns.
  - *Case study*: The parent agent proposes a hypothesis about a bug. The user responds: *"use spawn-subagent to check if the hypothesis is sound"*. The parent agent sets `Overall Goal: fix the bug` and parrots `User Intent: check if the hypothesis is sound`.
- **Why it fails**: The subagent context operates with total amnesia. Copying `"the hypothesis"` passes an empty pronoun with no referent. The subagent has no access to parent chat history, has no idea what hypothesis was proposed, and cannot execute the task.
- **Correct action**: Apply the Self-Sufficiency Test. Materialize the exact hypothesis mechanics and the bug symptoms into `Delegated Subject`. Set `Authentic User Intent` to verifying that specific hypothesis against first principles.

### 2. Meta-Parroting (Echoing Orchestration Commands)
- **What happens**: Relaying parent orchestration directives as user intent (writing `User Intent: use spawn-subagent to...`).
- **Why it fails**: Conflates the tool mechanism with the engineering goal.
- **Correct action**: Strip tool invocations and extract the authentic engineering outcome.

### 3. Fabricating Criteria (Synthetic Constraints)
- **What happens**: Adding unrequested acceptance criteria, rigid frameworks, or invented rules to make the prompt look "structured".
- **Why it fails**: Corrupts user intent and causes false audit friction against imaginary constraints.
- **Correct action**: Distinguish between *materializing conversational context* (mandatory) and *inventing unstated constraints* (forbidden).

### 4. Recency Bleed (Commit History Leak)
- **What happens**: Asking the subagent to verify recent parent edits or PR changes (*"Did removing X leave residuals?"*).
- **Why it fails**: Biases the subagent toward past diffs rather than steady-state correctness.
- **Correct action**: Frame the objective neutrally against the target contract.

### 5. Pre-Barking & Anchoring Bias (The `e.g.` Trap)
- **What happens**: Supplying `(e.g., X, Y)` in the prompt, where X and Y are the exact scenarios or fields the parent agent already thought of.
- **Why it fails**: Causes anchoring bias. The subagent expends its reasoning budget verifying the cases you already solved (zero new value) while remaining blind to unhandled cases Z and W that you never conceived.
- **Correct action**: Ban `e.g.`, `such as`, and `like`. Mandate that the subagent deduce all domain failure modes and boundary conditions from first principles.

### 6. False Target Concealment
- **What happens**: Withholding the subject of investigation or problem context under the misconception that giving any context is "spoon-feeding".
- **Why it fails**: Forces the subagent to guess what domain or problem it is supposed to inspect.
- **Correct action**: Clearly specify the *Subject Under Review / Problem State* while leaving the *files, paths, and proof discovery* completely open to the subagent.

### 7. Missing the Mandate (Rubber-Stamping)
- **What happens**: Giving an objective without an explicit operational posture (license to doubt).
- **Why it fails**: Subagents naturally seek confirmation of the parent's work.
- **Correct action**: Explicitly assign an external persona with a zero-trust baseline.

### 8. Direct Artifact Path Assumption (Tooling Failure)
- **What happens**: Instructing the subagent to write directly to `<parent-conversation-dir>/<artifact_name>.md`.
- **Why it fails**: Tooling enforces creation within `<subagent-id>`.
- **Correct action**: Instruct generation in local sandbox, then `cp` / `mv` to parent directory.

---

## Ongoing Subagent Communication Protocol (`send_message`)

When following up, redirecting, or assigning subsequent tasks to an active subagent via `send_message`:

### 1. Zero Redundancy & Minimal Reference
- **Do Not Rehash**: Never repeat, summarize, or re-explain context, file structures, or findings that the subagent already identified or holds in its conversation transcript.
- **Minimal Pointers**: Reference prior context using the absolute minimum words necessary to disambiguate the target: cite only the finding index, artifact section, or distinct failure identifier without re-explaining the underlying mechanics.

### 2. Directive Formulation Rules
Construct follow-up messages using explicit, outcome-driven rules:
- **Lead with the Direct Outcome**: State the concrete deliverable, verification check, or implementation goal as the opening clause.
- **Strip Meta-Language**: Eliminate orchestration filler, polite conversational padding, and procedural commentary (*"Now that you finished X, please do Y..."* -> State Y directly).
- **Enforce Authentic Constraints Only**: Include only genuine technical constraints and success criteria. Never invent arbitrary checklist items or speculative acceptance steps.
- **Zero Leading Anchors**: Avoid pre-supposing the exact solution or naming narrow hypothetical causes. Leave the proof and validation pathway fully autonomous.
