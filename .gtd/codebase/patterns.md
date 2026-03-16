# Patterns And Conventions

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Verified Patterns

### Agent Configuration (YAML Frontmatter)

- Description: Agents are defined in Markdown files with a YAML frontmatter containing metadata like name, description, tools, and model.
- Why it appears to exist: To provide a structured way to configure agent behavior and tool access.
- Examples: `.gemini/agents/research.md`, `.gemini/agents/performance.md`
- Evidence: `.gemini/agents/research.md:1-40`

### XML-Structured Queries

- Description: Agents expect their `query` parameter to be formatted as XML with specific tags like `<scope>`, `<objective>`, and `<context>`.
- Why it appears to exist: To provide clear, machine-parsable instructions to the agent.
- Examples: `.gemini/agents/research.md`, `.gemini/agents/security.md`
- Evidence: `.gemini/agents/research.md:10-25`

### Skill Workflow Definition

- Description: Skills are defined in Markdown files with a YAML frontmatter and a detailed, step-by-step workflow.
- Why it appears to exist: To guide the agent through complex, multi-stage tasks.
- Examples: `.gemini/skills/doc-coauthoring/SKILL.md`, `skills/research/SKILL.md`
- Evidence: `.gemini/skills/doc-coauthoring/SKILL.md:1-10`
