<!-- Imported from: ./agents.md -->
# Domain: Agents

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Purpose

Defines specialized AI agent roles with specific tools, models, and configurations to perform targeted tasks within the GTD framework.

Evidence: `.gemini/agents/research.md`, `.codex/agents/architecture.toml`

## Key Files

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `.gemini/agents/research.md` | Codebase behavior research and documentation. | `.gemini/agents/research.md:2-5` |
| `.gemini/agents/performance.md` | Performance auditing and bottleneck identification. | `.gemini/agents/performance.md` |
| `.gemini/agents/security.md` | Security auditing and vulnerability assessment. | `.gemini/agents/security.md` |

## Important Flows

### Agent Invocation

1. A command or workflow specifies an agent to use.
2. The agent's configuration (tools, model) is loaded.
3. The agent receives a structured XML query.
4. The agent executes tools and returns a result.

Evidence: `.gemini/commands/bootstrap.toml:1-20`

## Dependencies

- `skills/` — Agents use skills to extend their capabilities. Evidence: `.gemini/agents/research.md:30`
- `tools` — Agents have access to a set of core tools (read_file, write_file, etc.). Evidence: `.gemini/agents/research.md:28`
<!-- End of import from: ./agents.md -->
<!-- Imported from: ./commands.md -->
# Domain: Commands

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Purpose

Defines structured commands that map user requests to specific agents, workflows, and prompts.

Evidence: `.gemini/commands/bootstrap.toml`, `.gemini/commands/codebase-overview.toml`

## Key Files

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `.gemini/commands/bootstrap.toml` | Initializes project backlog and journal. | `.gemini/commands/bootstrap.toml:1` |
| `.gemini/commands/codebase-overview.toml` | Generates codebase documentation. | `.gemini/commands/codebase-overview.toml` |
| `.gemini/commands/spec.toml` | Defines a feature or task specification. | `.gemini/commands/spec.toml` |

## Important Flows

### Command Execution

1. User invokes a command (e.g., `/bootstrap`).
2. The CLI loads the corresponding `.toml` file.
3. The command's `prompt` and `role` are passed to the specified agent.
4. The agent executes the task and returns the result.

Evidence: `.gemini/commands/bootstrap.toml:1-20`

## Dependencies

- `agents` — Commands are executed by agents. Evidence: `.gemini/commands/bootstrap.toml:4`
- `workflows` — Commands can trigger or be part of workflows. Evidence: `.gemini/commands/codebase-overview.toml`
<!-- End of import from: ./commands.md -->
<!-- Imported from: ./skills.md -->
# Domain: Skills

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Purpose

Provides specialized capabilities and structured workflows that agents can use to perform complex, multi-stage tasks.

Evidence: `.gemini/skills/doc-coauthoring/SKILL.md`, `skills/research/SKILL.md`

## Key Files

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `.gemini/skills/doc-coauthoring/SKILL.md` | Guided document co-authoring workflow. | `.gemini/skills/doc-coauthoring/SKILL.md:1-10` |
| `skills/research/SKILL.md` | Codebase archaeology and research workflow. | `skills/research/SKILL.md` |
| `skills/review-plan/SKILL.md` | Pre-execution plan review and validation. | `skills/review-plan/SKILL.md` |

## Important Flows

### Skill Activation

1. An agent or command calls `activate_skill`.
2. The skill's Markdown definition is loaded.
3. The agent follows the workflow instructions in the skill definition.

Evidence: `.gemini/agents/research.md:30`

## Dependencies

- `tools` — Skills use core tools to perform their tasks. Evidence: `.gemini/skills/doc-coauthoring/SKILL.md:150`
<!-- End of import from: ./skills.md -->
