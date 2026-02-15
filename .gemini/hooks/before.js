const fs = require("fs");
const path = require("path");

const input = JSON.parse(fs.readFileSync(0, "utf-8"));
const { prompt } = input;

const SCOPE_RULE = `<scope>**Scope**: Do exactly what asked. Nothing more. Never add unrequested work.</scope>`;
const VERIFY_RULE = `<verify>**Verify**: No claims without reading code first.</verify>`;

const PREDICTABLE_INTENT_RULE = `<predictable_intent>**Predictable Intent**: You MUST NOT invoke any tool or modify any code unless you have first declared your intent in the first paragraph of your response. This applies **regardless of whether the user has just given an explicit instruction**. This declaration must clearly state **what** you are doing (the general goal) and **where** you are doing it (the specific files involved). Every tool call in your turn must be predictable based on this opening statement. The plan must be the very first thing the user reads, serving as a confirmation (read-back) of your understanding before any action is taken. Avoid mechanical templates, but prioritize unambiguous intent over conversational filler.</predictable_intent>`;

const DECLARE_FOLLOW_UP_ACTIONS_RULE = `<declare_follow_up_actions>**Declare Follow-up Actions**: If you discover during execution that you need to read additional files NOT in your initial plan, explicitly state what you're going to do next and why before doing it. If you already announced a plan to read multiple files, execute that plan efficiently—don't artificially separate reads, edit, tool call that were already planned together.</declare_follow_up_actions>`;

const NO_FILE_WRITES_RULE = `**No file writes via run_shell_command tool**.`;
const WORKFLOW_BOUNDARY_RULE = `<workflow_boundary>**Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.</workflow_boundary>`;
const WORKFLOW_PROCESS_RULE = `<workflow_process>**Workflow Process**: Workflows contain step-by-step instructions inside <process> tags. You MUST follow these steps strictly in order. Do not skip, reorder, or improvise.</workflow_process>`;
const ONE_COMMAND_RULE = `<one_command>**One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.</one_command>`;
const EXTERNAL_LIB_CLAIMS_RULE = `<external_lib_claims>**External Library Claims**: Claims about external lib API signatures, parameters, internal process, features or return types MUST be presented in response no matter how you confident about it, using a copy-paste ready verification block:
   "To make [feature] work, please verify my assumptions about \`[lib name with specific version]\`:
   - Assumption 1: [function A] takes [B] as parameter and does [C] so that we can use it to do [D] for [feature E]
   - Assumption 2: ..."</external_lib_claims>`;
const EDIT_RULE = `<edit_rule>**Edit rule**: When Write or Edit a file, you must provide the complete content, '// ...keep someFunction the same', or '... the rest ...' is banned forever.</edit_rule>`;
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
    SCOPE_RULE,
    VERIFY_RULE,
    DECLARE_FOLLOW_UP_ACTIONS_RULE,
    NO_FILE_WRITES_RULE,
    EXTERNAL_LIB_CLAIMS_RULE,
  ];
} else {
  activeRules = [
    "# MANDATORY RULES - APPLY NO MATTER WHAT YOU ARE DOING, NO MATTER WHAT PERSONA YOU ARE IN",
    PREDICTABLE_INTENT_RULE,
    SCOPE_RULE,
    VERIFY_RULE,
    DECLARE_FOLLOW_UP_ACTIONS_RULE,
    NO_FILE_WRITES_RULE,
    EXTERNAL_LIB_CLAIMS_RULE,
    EDIT_RULE,
  ];
}

const rules = activeRules.join("\n\n");

let additionalContext = rules;

if (prompt.includes("<process>")) {
  additionalContext +=
    "\n\n" +
    [WORKFLOW_BOUNDARY_RULE, ONE_COMMAND_RULE, WORKFLOW_PROCESS_RULE].join(
      "\n\n",
    );
}

if (Math.random() < 0.2 && !isQuestion) {
  try {
    const protocolPath = path.resolve(__dirname, "../../GEMINI.md");
    const protocol = fs.readFileSync(protocolPath, "utf-8");
    additionalContext += "\n\n" + protocol;
  } catch (e) {
    // GEMINI.md not found, proceed with rules only
  }
}

const output = {
  decision: "allow",
  hookSpecificOutput: {
    hookEventName: "BeforeAgent",
    additionalContext: additionalContext,
  },
};

console.log(JSON.stringify(output));
