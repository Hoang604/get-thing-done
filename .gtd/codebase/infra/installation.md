# Infrastructure: Installation

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Purpose

Provides scripts and logic for bootstrapping the GTD framework, installing agent components, and configuring the environment.

Evidence: `install-gemini.sh`, `install.sh`, `install-codex.sh`

## Interfaces

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `install-gemini.sh` | Installs Gemini-specific commands, agents, and skills. | `install-gemini.sh:4-15` |
| `install.sh` | General framework installation to a target directory. | `install.sh:4-10` |
| `install-codex.sh` | Installs Codex-specific components. | `install-codex.sh` |

## Integration Points

- `~/.gemini/` — Global installation target for Gemini components. Evidence: `install-gemini.sh:10`
- `./.gemini/` — Local project installation target. Evidence: `install-gemini.sh:9`

## Operational Notes

- The installation scripts use `set -e` for error handling. Evidence: `install-gemini.sh:2`
- Scripts support both local and global installation flags. Evidence: `install-gemini.sh:13-15`
