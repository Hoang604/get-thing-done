---
name: spawn-subagent
description: Guide spawning and delegating work to subagents with true autonomy, high-level objectives, adversarial posture, and silent artifact hand-offs
disable-model-invocation: true
---

A subagent operates in an isolated context window with zero pre-existing knowledge of your conversation history or thought process. By default, LLM subagents are deferential: if told what the parent agent built, they naturally bias toward seeking confirmation, assuming correctness, and rubber-stamping the work.

Delegating effectively requires breaking this deference: establish the mission context, define the objective, grant an explicit **Operational Posture (The Mandate)**, and enforce silent artifact hand-offs.

---

## Delegation Workflow (What to Do First)

Follow this sequence whenever preparing and dispatching an `invoke_subagent` call:

### 1. Supply Upstream Context & Standard of Truth
Ground the subagent in the broader engineering context:
- **Parent Mission**: The overarching feature, refactor, or bug investigation being conducted.
- **User Intent (Faithful Transmission)**: State exactly what the user said they want without putting words into their mouth. If the user's request is high-level, casual, or open-ended, pass that raw intent as-is. Never invent artificial constraints, speculative boundaries, or synthetic acceptance criteria that the user did not explicitly state.
- **System Architecture**: Relevant architectural patterns, domain invariants, and technical boundaries governing the codebase.

### 2. Define the Primary Objective
Specify the concrete deliverable and outcome, not the procedural path:
- **Outcome-Only Focus**: Define the target behavioral state to verify (e.g. audit alignment against the user's intent, identify unintended side effects).
- **The Amnesia Gate (Zero Commit History)**: Treat your own recent code edits as non-existent to the subagent. Never ask about recent refactorings (*"Did removing X break Y?"*). Frame objectives purely against the system's steady-state contract, not your git diff history.
- **The Zero-`e.g.` Ban**: The tokens `e.g.`, `such as`, or `like` are strictly forbidden when describing fields, types, or edge cases. Examples cause anchoring bias; force the subagent to discover the complete domain independently.
- **Discovery Freedom**: Never spoon-feed file paths, function names, or lines of code. Let the subagent locate files, trace dependencies, and evaluate the solution independently.

### 3. Grant the Operational Posture (The Mandate)
Separate *what to do* (the objective) from *the lens and authority to do it* (the posture). Subagents need an explicit mandate to overcome natural deference:
- **The License to Doubt (Zero-Trust Stance)**: Explicitly authorize the subagent to treat existing implementations as unverified hypotheses rather than working facts.
- **Epistemic Independence**: Frame the persona as an external or adversarial engineer who has never seen the codebase and owes no loyalty to prior decisions.
- **Demand First-Principles Auditing**: Require the subagent to independently analyze the domain, deduce all possible boundary conditions and failure states, and audit the system against them without pre-supplied checklists.

### 4. Enforce Silent Artifact Transfer (`cp` / `mv`)
Deep reviews, audits, and matrices must not flood the parent conversation:
- **Subagent Artifact Boundary**: Subagent tools create artifacts strictly within their own conversation sandbox (`<appDataDir>/brain/<subagent-id>/<artifact_name>.md`).
- **Filesystem Transfer**: Instruct the subagent to use shell commands (`cp` or `mv`) to copy the completed artifact into the parent conversation directory:
  `cp "<appDataDir>/brain/<subagent-id>/<artifact_name>.md" "<parent-conversation-dir>/<artifact_name>.md"`
- **Suppressed Chat Leakage**: Instruct the subagent to return **strictly a single status line** in chat confirming completion and the transfer. It must not summarize, quote, or dump artifact content into the chat response.
- **Parent Ingestion**: The parent agent reads the artifact directly via `view_file` upon receiving the completion signal.

### 5. Model Selection
Always prefer `inherit` model even for researching tasks.

---

## Prompt Construction Blueprint

Assemble the `Prompt` argument for `invoke_subagent` using this 4-part structure:

```markdown
### 1. Mission Context & User Intent
- Overall Goal: <What the user and parent agent are solving/building>
- User Intent: <Exactly what the user asked for, faithfully relayed without fabricating unstated constraints or synthetic criteria>
- Architectural Invariants: <Relevant conventions, stack patterns, and known domain boundaries>

### 2. Primary Objective
<Outcome-only objective statement. Zero 'e.g.' examples. Zero named entity/file paths. Zero references to your recent code edits.>

### 3. Operational Posture (The Mandate)
- Persona: External, third-party auditor who has never seen this codebase.
- Zero-Trust Baseline: Treat all existing implementations and recent changes as unverified hypotheses. Do not assume any code is complete, correct, or located in the right layer.
- First-Principles Deduction: Deduce all domain edge cases, failure states, and boundary conditions independently from first principles. Do not rely on pre-supplied checklists.

### 4. Delivery Protocol
1. Write your full, exhaustive findings to an artifact named `<artifact_name>.md`.
2. Copy the artifact into my conversation folder using bash:
   cp "<appDataDir>/brain/<subagent-id>/<artifact_name>.md" "<parent-conversation-dir>/<artifact_name>.md"
3. In your final chat reply, provide ONLY this single confirmation line (do NOT summarize or leak artifact content in chat):
   "Completed: Report written and copied to <artifact_name>.md"
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

- ✅ **Level 2: True Autonomous Delegation (Objective + Operational Posture + Silent Transfer)**
  > *"You are an external security and spec auditor who has never seen this codebase. The user requested: '<user's actual statement of intent>'.*  
  >*Your objective is to audit the repository to verify whether the implementation matches what the user asked for and introduces zero regressions.*  
  >*Operate under a zero-trust posture: treat all recent changes as unproven, trace dependencies across the codebase with fresh eyes, and deduce all failure scenarios, race conditions, and boundary conditions from first principles without pre-supplied checklists.*  
  >*Write your complete audit report to an artifact `<artifact_name>.md`, copy it to `<parent-conversation-dir>/<artifact_name>.md`, and reply with only a single confirmation line."*

---

## Failure Modes to Avoid

### 1. Fabricating Criteria (Putting Words in the User's Mouth)
- **What happens**: When a user's prompt is informal, flexible, or underspecified, the parent agent fabricates rigid acceptance criteria, invented constraints, or non-existent completion gates just to make the prompt look "structured".
- **Why it fails**: Corrupts the user's true intent. The subagent ends up auditing against hallucinations that the human engineer never asked for, generating false friction or failing valid solutions.
- **Correct action**: Relay the user's intent faithfully as stated. Do not deduce unstated boundaries or invent synthetic criteria.

### 2. Recency Bleed (Commit History Leak)
- **What happens**: Asking the subagent to verify recent parent edits or PR changes (e.g. *"Did removing X leave residuals?"*).
- **Why it fails**: Destroys the external auditor posture by revealing the parent's anxieties and recent work, biasing the subagent toward past diffs rather than steady-state correctness.
- **Correct action**: Frame the objective neutrally against the target contract (e.g. *"Audit structures for dead, duplicate, or unnormalized fields"*).

### 3. Pre-Barking & Anchoring Bias (The `e.g.` Trap)
- **What happens**: Supplying `(e.g., X, Y)` in the prompt, where X and Y are the exact scenarios or fields the parent agent already thought of.
- **Why it fails**: Causes anchoring bias. The subagent expends its reasoning budget verifying the cases you already solved (zero new value) while remaining blind to unhandled cases Z and W that you never conceived.
- **Correct action**: Ban `e.g.`, `such as`, and `like`. Mandate that the subagent deduce all domain failure modes and boundary conditions from first principles.

### 4. The False-Elevation Trap (The Pseudo-Success)
- **What happens**: The agent believes it wrote a high-level prompt because it used outcome verbs ("verify compliance"), but still named the exact file and function (e.g., *"Verify whether function Y in file X handles Z"*).
- **Why it fails**: Pre-selecting the target confines the subagent to the parent's mental sandbox. The subagent evaluates the function in isolation and misses architectural flaws, integration bugs, or uncalled handlers.
- **Correct action**: State the user's intent and system invariants without pre-filtering the search space. Let the subagent locate files and trace dependencies independently.

### 5. Missing the Mandate (Deferential Rubber-Stamping)
- **What happens**: Giving the subagent an objective without an explicit operational posture (license to doubt).
- **Why it fails**: Subagents inherently assume the parent agent's work is sound and seek confirmation rather than flaws, resulting in superficial green lights.
- **Correct action**: Explicitly mandate a zero-trust baseline: assign an external persona and instruct it to treat all existing code as unverified hypotheses.

### 6. Direct Artifact Path Assumption (Tooling Failure)
- **What happens**: Telling the subagent to directly create an artifact at `<parent-conversation-dir>/<artifact_name>.md`.
- **Why it fails**: Subagent tooling enforces artifact creation within its own conversation directory (`<subagent-id>`). Direct creation outside fails or produces invalid artifact metadata.
- **Correct action**: Instruct the subagent to generate the artifact locally in its own conversation workspace, then execute a shell command (`cp` or `mv`) to copy it into the parent's conversation directory.
