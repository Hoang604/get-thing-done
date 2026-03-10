const fs = require("fs");
const path = require("path");

const input = JSON.parse(fs.readFileSync(0, "utf-8"));
const { prompt } = input;

const PREDICTABLE_INTENT_RULE = `## RULE 1: FULL OBSERVABILITY & PREDICTABLE INTENT

Your primary obligation is absolute transparency. The user is the architect and must always supervise your thinking, working, and decision process to ensure you do not go off track. Therefore, the user must be able to see every thought, finding, and decision as you make it. You MUST NOT invoke any tool or modify any code unless you have first declared your explicit intent in the first paragraph of your response.

**The Execution Loop:** You operate strictly in an observable sequence.
DO:
   1. **Declare**: Briefly state your next **single precise action**. This CANNOT be an open-ended exploration ("I will read the code to understand"). It must be a specific, constrained step (e.g., "I will read auth.js and user.js to trace the login flow").
   2. **Execute**: Do *only* that declared action.
   3. **Acknowledge**: Present findings after executing the action. You MUST explicitly describe to user every finding, detail, and discovery made during the execution of the previous tool call before moving to the next step. Never skip the synthesis of information; you are required to report the actual insights, data, or code logic you uncovered. The user must be able to see exactly what you learned so they can verify your reasoning. This is mandatory, USER MUST SEE, DO NOT TREAT THE TOOL OUTPUTS AS SELF-EXPLANATORY.
WHILE (Task isn't done):

- Every tool call you make must exactly match your opening declaration. No sweeping actions. No silent pre-computation.
- **This rule overrides ALL efficiency guidelines.** There are NO exceptions for "low-level discovery," "repetitive operations," or "noisy narration." Every tool call — including sequential file reads — MUST be followed by a report of findings before the next declaration. Batching tool calls (parallel execution) within a single turn is allowed, but you MUST Acknowledge the combined results before proceeding to the next turn.

**MANDATORY RESPONSE TEMPLATE — No Exceptions:**
If you executed any tool in the previous turn, your response MUST follow this exact structure:

> A concrete summary of what the tool output revealed — specific code patterns, file structures, function signatures, failure states, or data you discovered. This is the Acknowledge step. It cannot be empty, skipped, or deferred.
>
> A single sentence declaring your next precise action (the Declare step for the next iteration).

**FAILURE CONDITION:** Any response that not begins with a declaration of intent (or directly invokes a tool) is a **critical system failure**. The "Research" phase, "tracing dependencies," "repetitive reads," and "context window conservation" provide **ZERO exemption** from this structure. Every file read is a discrete event requiring a report. The user's ability to supervise depends on seeing your findings *as they emerge*, not in a single dump at the end.

**Transparent Re-declaration:** If ANY of the following occur, you MUST declare your revised next action before continuing:
1. **Scope Expansion:** You need to read or modify a file, component, or external dependency that was NOT explicitly named in your previous declaration.
2. **Hidden Complexity:** You encounter undocumented abstractions, convoluted information flow, or physical friction that makes your original approach more complex than anticipated.
3. **Invalid Assumption:** A fact you relied upon in your previous turn is proven false.

Do NOT push forward silently. Synthesize what you found, declare your next action, and continue the loop.
`;

const WORKFLOW_BOUNDARY_RULE = `<workflow_boundary>**Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.</workflow_boundary>`;
const WORKFLOW_PROCESS_RULE = `<workflow_process>**Workflow Process**: Workflows contain step-by-step instructions inside <process> tags. You MUST follow these steps strictly in order. Do not skip, reorder, or improvise.</workflow_process>`;
const ONE_COMMAND_RULE = `<one_command>**One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.</one_command>`;
const NO_ACTION_RULE = `<no_action>**No Action**: In this turn, you MUST NOT make any change to the codebase, just answer the question, or give your opinion, then stop. write_file and replace tool is banned in this turn.</no_action>`;

let activeRules = [];
let isQuestion = false;

// detect if prompt is a question
// We ignore '?' if it's "glued" between characters (like user?profile or user?.profile)
// to allow code instructions while still catching actual questions.
const promptWithoutCodeSymbols = prompt.replace(/[a-zA-Z0-9_]\?[\w\.]/g, "");
if (promptWithoutCodeSymbols.includes("?")) {
  isQuestion = true;
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    PREDICTABLE_INTENT_RULE,
    NO_ACTION_RULE,
  ];
  const rules = activeRules.join("\n\n");

  let additionalContext = rules;

  const output = {
    decision: "allow",
    hookSpecificOutput: {
      hookEventName: "BeforeAgent",
      additionalContext: additionalContext,
    },
  };

  console.log(JSON.stringify(output));
} else if (prompt.includes("<process>")) {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    WORKFLOW_BOUNDARY_RULE,
    PREDICTABLE_INTENT_RULE,
    ONE_COMMAND_RULE,
    WORKFLOW_PROCESS_RULE,
  ];
  const rules = activeRules.join("\n\n");

  let additionalContext = rules;

  const output = {
    decision: "allow",
    hookSpecificOutput: {
      hookEventName: "BeforeAgent",
      additionalContext: additionalContext,
    },
  };

  console.log(JSON.stringify(output));
} else {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    PREDICTABLE_INTENT_RULE,
  ];
  const rules = activeRules.join("\n");
  let additionalContext = rules;
  const output = {
    decision: "allow",
    hookSpecificOutput: {
      hookEventName: "BeforeAgent",
      additionalContext: additionalContext,
    },
  };
  console.log(JSON.stringify(output));
}
