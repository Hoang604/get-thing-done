# Entrypoints

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

| Entrypoint | Type | File | Purpose | Evidence |
| ---------- | ---- | ---- | ------- | -------- |
| `install-gemini.sh` | Script | `install-gemini.sh` | Installs Gemini CLI components. | `install-gemini.sh:4` |
| `install.sh` | Script | `install.sh` | General GTD framework installation. | `install.sh:4` |
| `bootstrap` | Command | `.gemini/commands/bootstrap.toml` | Initializes project backlog. | `.gemini/commands/bootstrap.toml:1` |
| `codebase-overview` | Command | `.gemini/commands/codebase-overview.toml` | Generates codebase documentation. | `.gemini/commands/codebase-overview.toml` |

## Startup Flows

### Gemini CLI Installation

1. User runs `./install-gemini.sh`.
2. Script copies commands, agents, and skills to the target location.
3. Optionally sets up global configuration.

Evidence: `install-gemini.sh:4-15`

### Project Bootstrapping

1. User runs `bootstrap` command.
2. `bootstrap.toml` invokes the project initializer agent.
3. Agent reads architecture docs and creates `BACKLOG.md` and `JOURNAL.md`.

Evidence: `.gemini/commands/bootstrap.toml:1-20`
