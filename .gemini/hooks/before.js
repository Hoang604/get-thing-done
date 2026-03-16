const fs = require("fs");

const input = JSON.parse(fs.readFileSync(0, "utf-8"));
const { prompt } = input;

const PREDICTABLE_INTENT_RULE = `## RULE 1: PREDICTABLE INTENT

Before any tool call or code change, state your next single concrete action in the first sentence.

Rules:
- No vague declarations like "I will explore the codebase"
- No silent tool calls
- No scope expansion without re-declaring it
- Do not treat tool output as self-explanatory; summarize the important findings
- If a previous assumption was wrong, say so before continuing
- Before a write tool, briefly explain why this change is the right edit before executing it
- If the previous step used a tool, your next reply must include:
  For read tools:
    Findings: what the tool output revealed
    Next action: one concrete next step
  For write tools:
    Change made: what the tool changed
    Next action: one concrete next step
  For execute tools:
    Result: what happened and what it means
    Next action: one concrete next step
`;

const WORKFLOW_BOUNDARY_RULE = `**Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.`;
const WORKFLOW_PROCESS_RULE = `**Workflow Process**: Workflows contain step-by-step instructions inside <process> tags. You MUST follow these steps strictly in order. Do not skip, reorder, or improvise.`;
const ONE_COMMAND_RULE = `**One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.`;
const NO_ACTION_RULE = `**No Action**: In this turn, you MUST NOT make any change to the codebase, just answer the question, or give your opinion, then stop. write_file and replace tool is banned in this turn.`;

function emitRules(rules, separator = "\n\n") {
  console.log(
    JSON.stringify({
      decision: "allow",
      hookSpecificOutput: {
        hookEventName: "BeforeAgent",
        additionalContext: rules.join(separator),
      },
    }),
  );
}

let activeRules = [];

// detect if prompt is a question
// We ignore '?' if it's "glued" between characters (like user?profile or user?.profile)
// to allow code instructions while still catching actual questions.
const promptWithoutCodeSymbols = prompt.replace(/[a-zA-Z0-9_]\?[\w\.]/g, "");
if (promptWithoutCodeSymbols.includes("?")) {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    PREDICTABLE_INTENT_RULE,
    NO_ACTION_RULE,
  ];
  emitRules(activeRules);
} else if (prompt.includes("<process>")) {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    WORKFLOW_BOUNDARY_RULE,
    PREDICTABLE_INTENT_RULE,
    ONE_COMMAND_RULE,
    WORKFLOW_PROCESS_RULE,
  ];
  emitRules(activeRules);
} else {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    PREDICTABLE_INTENT_RULE,
  ];
  emitRules(activeRules, "\n");
}
