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
