const fs = require("fs");

const input = JSON.parse(fs.readFileSync(0, "utf-8"));
const { prompt } = input;

const PREDICTABLE_INTENT_RULE = `## RULE 1: PREDICTABLE INTENT

Report your intent before tool call.
`;

const WORKFLOW_BOUNDARY_RULE = `**Workflow Boundary**: Stop at <forced_stop>. No auto-chain. Suggest next steps, do not execute.`;
const WORKFLOW_PROCESS_RULE = `**Workflow Process**: Follow <process> steps strictly. No skip. No improvise.`;
const ONE_COMMAND_RULE = `**One Command Per Turn**: Execute invoked workflow only. No chain /plan → /execute.`;
const NO_ACTION_RULE = `**No Action**: No code change, no fix, answer user question`;

function emitRules(rules, separator = "\n\n") {
  console.log(
    JSON.stringify({
      decision: "allow",
      hookSpecificOutput: {
        hookEventName: "BeforeAgent",
        additionalContext: `Hook: BeforeAgent\n\n${rules.join(separator)}`,
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
    "# MANDATORY RULES",
    PREDICTABLE_INTENT_RULE,
    NO_ACTION_RULE,
  ];
  emitRules(activeRules);
} else if (prompt.includes("<process>")) {
  activeRules = [
    "# MANDATORY RULES",
    WORKFLOW_BOUNDARY_RULE,
    PREDICTABLE_INTENT_RULE,
    ONE_COMMAND_RULE,
    WORKFLOW_PROCESS_RULE,
  ];
  emitRules(activeRules);
} else {
  activeRules = [
    "# MANDATORY RULES",
    PREDICTABLE_INTENT_RULE,
  ];
  emitRules(activeRules, "\n");
}
