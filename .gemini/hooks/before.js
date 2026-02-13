const fs = require("fs");
const path = require("path");

const input = JSON.parse(fs.readFileSync(0, "utf-8"));
const { prompt } = input;

const SCOPE_RULE = `**Scope**: Do exactly what asked. Nothing more. Never add unrequested work.`;
const VERIFY_RULE = `**Verify**: No claims without reading code first. Cite file:line or say "I don't know."`;

const PREDICTABLE_INTENT_RULE = `**Predictable Intent**: Start your response with a natural declaration of your plan. For simple questions, keep it conversational (e.g., "I'll check the auth flow"). For complex tasks, describe your complete approach upfront (e.g., "I'll read main.rs, config.rs, and consumer.rs to trace initialization"), then execute all planned actions in this turn. Avoid mechanical templates—sound human while being clear.`;

const PREDICTABLE_INTENT_RULE_NO_MAKE_CHANGE = `**Predictable Intent**: Answer naturally and directly. You may briefly frame your response (e.g., "Let me explain the difference" or "Here's why that happens") but avoid rigid preambles for simple questions. Just answer clearly, then stop.`;

const DECLARE_FOLLOW_UP_ACTIONS_RULE = `**Declare Follow-up Actions**: If you discover during execution that you need to read additional files NOT in your initial plan, explicitly state what you're going to do next and why before doing it. If you already announced a plan to read multiple files, execute that plan efficiently—don't artificially separate reads, edit, tool call that were already planned together.`;

const NO_FILE_WRITES_RULE = `**No file writes via run_shell_command tool**.`;
const WORKFLOW_BOUNDARY_RULE = `**Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.`;
const WORKFLOW_PROCESS_RULE = `**Workflow Process**: Workflows contain step-by-step instructions inside <process> tags. You MUST follow these steps strictly in order. Do not skip, reorder, or improvise.`;
const ONE_COMMAND_RULE = `**One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.`;
const EXTERNAL_LIB_CLAIMS_RULE = `**External Library Claims**: Claims about external lib API signatures, parameters, internal process, features or return types MUST be presented in response no matter how you confident about it, using a copy-paste ready verification block:
   "To make [feature] work, please verify my assumptions about \`[lib name with specific version]\`:
   - Assumption 1: [function A] takes [B] as parameter and does [C] so that we can use it to do [D] for [feature E]
   - Assumption 2: ..."`;
const EDIT_RULE = `**Edit rule**: When Write or Edit a file, you must provide the complete content, '// ...keep someFunction the same', or '... the rest ...' is banned forever.`;
const NO_ACTION_RULE = `**No Action**: In this turn, you MUST NOT make any change to the codebase, just answer the question, or give your opinion, then stop. write_file and replace tool is banned in this turn.`;

let activeRules = [];
let isQuestion = false;

// detect if prompt is a question
// We ignore '?' if it's "glued" between characters (like user?profile or user?.profile)
// to allow code instructions while still catching actual questions.
const promptWithoutCodeSymbols = prompt.replace(/[a-zA-Z0-9_]\?[\w\.]/g, "");
if (promptWithoutCodeSymbols.includes("?")) {
  isQuestion = true;
  activeRules = [
    "# RULES",
    NO_ACTION_RULE,
    SCOPE_RULE,
    VERIFY_RULE,
    PREDICTABLE_INTENT_RULE_NO_MAKE_CHANGE,
    DECLARE_FOLLOW_UP_ACTIONS_RULE,
    NO_FILE_WRITES_RULE,
    EXTERNAL_LIB_CLAIMS_RULE,
  ];
} else {
  activeRules = [
    "# RULES",
    SCOPE_RULE,
    VERIFY_RULE,
    PREDICTABLE_INTENT_RULE,
    DECLARE_FOLLOW_UP_ACTIONS_RULE,
    NO_FILE_WRITES_RULE,
    WORKFLOW_BOUNDARY_RULE,
    WORKFLOW_PROCESS_RULE,
    ONE_COMMAND_RULE,
    EXTERNAL_LIB_CLAIMS_RULE,
    EDIT_RULE,
  ];
}

const rules = activeRules.join("\n\n");

let additionalContext = rules;

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
