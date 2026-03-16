# Architecture

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Tech Stack

| Layer | Technology | Evidence |
| ----- | ---------- | -------- |
| Language | Bash, JavaScript, Python | `install-gemini.sh`, `update-settings.js`, `merge_codex_config.py` |
| Runtime | Node.js, Bash | `update-settings.js`, `install-gemini.sh` |
| Framework | GTD Framework (Custom) | `install-gemini.sh:4` |

## Project Structure

- `.gemini/`: Gemini-specific agent, command, and skill definitions.
- `.codex/`: Codex-specific agent and skill definitions.
- `.claude/`: Claude-specific agent and skill definitions.
- `skills/`: Shared skill definitions.
- `workflows/`: Cross-cutting process definitions.
- `install*.sh`: Installation and bootstrapping scripts.

Evidence: `ls -la`

## Major Subsystems

### Agent Definitions

- Type: Domain
- Path: `.gemini/agents/`, `.codex/agents/`, `.claude/agents/`
- Purpose: Defines specialized AI agent roles with specific tools and configurations.
- Depends on: Skills, Tools
- Used by: Commands, Workflows
- Evidence: `.gemini/agents/research.md`

### Skill Definitions

- Type: Domain
- Path: `.gemini/skills/`, `.codex/skills/`, `.claude/skills/`, `skills/`
- Purpose: Provides specialized capabilities and workflows for agents.
- Depends on: Tools
- Used by: Agents
- Evidence: `.gemini/skills/doc-coauthoring/SKILL.md`

### Command Definitions

- Type: API
- Path: `.gemini/commands/`
- Purpose: Defines structured commands for interacting with agents and workflows.
- Depends on: Agents, Workflows
- Used by: CLI
- Evidence: `.gemini/commands/bootstrap.toml`
