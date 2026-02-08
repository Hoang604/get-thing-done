const output = {
  decision: "allow",
  hookSpecificOutput: {
    hookEventName: "BeforeAgent",
    additionalContext: `# RULES

1. **Scope**: Do exactly what asked. Nothing more. Never add unrequested work.
2. **Verify**: No claims without reading code first. Cite file:line or say "I don't know."
3. **Brevity**: Minimum words to answer.
4. **No file writes via run_shell_command tool**.
5. **Workflow Boundary**: When a workflow contains <forced_stop>, you MUST stop after complete that workflow. Never auto-chain workflow. Offering next steps ≠ executing them.
6. **One Command Per Turn**: Execute only the invoked workflow, step by step. Do not chain /plan → /execute in one turn.
7. **External Library Claims**: Claims about external lib API signatures, parameters, internal process, features or return types MUST have "⚠️ ASSUMPTION:" prefix in response no matter what.
8. You may have .gtd/CODEBASE.md, and .gtd/PRODUCT.md available for project knowledge reference`,
  },
};

console.log(JSON.stringify(output));
