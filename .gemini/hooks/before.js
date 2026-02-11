const fs = require("fs");
const path = require("path");

const rules = `# RULES

1. **Scope**: Do exactly what asked. Nothing more. Never add unrequested work.
2. **Verify**: No claims without reading code first. Cite file:line or say "I don't know."
3. **Brevity**: Minimum words to answer.
4. **No file writes via run_shell_command tool**.
5. **Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.
6. **Workflow Process**: Workflows contain step-by-step instructions inside <process> tags. You MUST follow these steps strictly in order. Do not skip, reorder, or improvise.
7. **One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.
8. **External Library Claims**: Claims about external lib API signatures, parameters, internal process, features or return types MUST be presented in response no matter how you confident about it, using a copy-paste ready verification block:
   "To make [feature] work, please verify my assumptions about \`[lib name with specific version]\`:
   - Assumption 1: [function A] takes [B] as parameter and does [C] so that we can use it to do [D] for [feature E]
   - Assumption 2: ..."
9. You may have .gtd/CODEBASE.md, and .gtd/PRODUCT.md available for project knowledge reference, read it to understand how the codebase is construct
10. **Edit rule**: When Write or Edit a file, you must provide the complete content, '// ...keep someFunction the same', or '... the rest ...' is banned forever.`;

let additionalContext = rules;

if (Math.random() < 0.1) {
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
