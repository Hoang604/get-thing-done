# Infrastructure: Workflows

**Generated:** 2026-03-16
**Last Updated:** 2026-03-16
**Last Verified:** 2026-03-16

## Purpose

Defines cross-cutting processes and workflows that coordinate multiple agents and tasks.

Evidence: `workflows/`, `.gemini/commands/codebase-overview.toml`

## Interfaces

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `workflows/codebase-overview.md` | Workflow for generating codebase documentation. | `workflows/codebase-overview.md` |
| `workflows/bootstrap.md` | Workflow for initializing a new project. | `workflows/bootstrap.md` |
| `workflows/spec.md` | Workflow for defining a feature specification. | `workflows/spec.md` |

## Integration Points

- `.gemini/commands/` — Commands often invoke specific workflows. Evidence: `.gemini/commands/codebase-overview.toml`
- `agents` — Workflows are executed by agents following the defined steps. Evidence: `workflows/codebase-overview.md`

## Operational Notes

- Workflows are defined in Markdown and use a structured process format. Evidence: `workflows/codebase-overview.md`
- Each workflow typically includes an objective, context, and step-by-step process. Evidence: `workflows/codebase-overview.md`
