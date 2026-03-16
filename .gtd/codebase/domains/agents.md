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
