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
