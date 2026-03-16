# Open Questions

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

- How are the different agent types (Gemini, Codex, Claude) coordinated?
  - Why unresolved: Only individual agent definitions were inspected.
  - Next place to inspect: `workflows/` or `install-gemini.sh` for coordination logic.

- What is the relationship between the shared `skills/` directory and the agent-specific `skills/` directories?
  - Why unresolved: Both exist but their precedence or merging logic is not yet clear.
  - Next place to inspect: `install-gemini.sh` or `update-settings.js`.

- How are the `workflows/*.md` files executed?
  - Why unresolved: They contain Markdown but their execution engine is not yet identified.
  - Next place to inspect: `.gemini/commands/` for workflow-related commands.
