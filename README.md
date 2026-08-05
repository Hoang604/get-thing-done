# Get-Thing-Done (GTD) Framework - Antigravity

Systematic agent workflows that enforce deep architectural reasoning over fast code generation—ensuring AI builds exactly what you want with zero-regression reliability.

## Antigravity Installation

### Global Install (available everywhere)

**Linux/macOS:**

```bash
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp && chmod +x *.sh && ./install.sh
cd .. && rm -rf gtd-temp
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/Hoang604/get-thing-done.git gtd-temp
cd gtd-temp; .\install.ps1
cd ..; Remove-Item -Recurse -Force gtd-temp
```

## Primary Workflows (Daily Use)

Systematic sequence of skills for rigorous development, auditing, and delivery:

> [!NOTE]
> Every skill listed below has an identical corresponding slash command available in global workflows (`.gemini/config/global_workflows/`). For example, invoking `/propose-plan` runs the exact same logic as the `propose-plan` skill.

### 1. Core Execution
- **[confirm](.gemini/skills/confirm/SKILL.md)**: Relentless interview to rigorously synchronize language, context, and system topology from top to bottom before execution.
- **[execute](.gemini/skills/execute/SKILL.md)**: Execute an approved Alignment Contract.
- **[propose-commit](.gemini/skills/propose-commit/SKILL.md)**: Propose a conventional commit message for the current changes.

### 2. Planning & Architecture
- **[propose-plan](.gemini/skills/propose-plan/SKILL.md)**: Gather context and propose architectural approaches with clear trade-offs before drafting a plan.
- **[draft-plan](.gemini/skills/draft-plan/SKILL.md)**: Draft formal `implementation_plan.md` artifact using EARS syntax with zero-prose literal contracts and seam test matrix.

### 3. Auditing & Stress Testing
- **[stress-test](.gemini/skills/stress-test/SKILL.md)**: Audit agent-produced work across operating regimes with zero-regression fixes.

### 4. Code Review & Verification
- **[code-review](.gemini/skills/code-review/SKILL.md)**: Take scope, review code, and return a structured architectural report.
- **[verify-issue](.gemini/skills/verify-issue/SKILL.md)**: Trace codebase to verify whether issues flagged in code review are false positives.

### 5. Analysis & Rule Improvement
- **[propose-rules](.gemini/skills/propose-rules/SKILL.md)**: Analyze agent trajectory or codebase artifacts for decision flaws and propose global or project-scoped rule improvements without editing files.
- **[explain](.gemini/skills/explain/SKILL.md)**: Explain code in a causal chain when analyzing a slice or feature.
- **[explain-architecture](.gemini/skills/explain-architecture/SKILL.md)**: Explain the skeleton of the architecture to build the global frame for understanding the codebase.

### 6. Self-Review Loop
- **[awareness](.gemini/skills/awareness/SKILL.md)**: Write `goal.md` and execute the self-review verification loop for non-trivial tasks. Only work for Antigravity CLI, because Antigravity IDE don't have subagent.

### 7. Testing & Verification Suites
- **[create-test](.gemini/skills/create-test/SKILL.md)**: Design repo-specific test strategy and write deterministic tests catching real boundary and invariant bugs at clean external seams.
- **[create-postman-collection](.gemini/skills/create-postman-collection/SKILL.md)**: Design and write importable Postman collections with deterministic request flows, schema-validated responses, and explicit prerequisite discovery.

### 8. Specification & Task Breakdown
- **[spec](.gemini/skills/spec/SKILL.md)**: Relentlessly interview to identify domain requirements and edge cases in EARS syntax without code leakage.
- **[to-ticket](.gemini/skills/to-ticket/SKILL.md)**: Break a confirmed `./.gtd/<task_name>/SPEC.md` into a set of tracer-bullet tickets, mapping domain concepts to codebase seams with explicit blocking edges published to `./.gtd/<task_name>/tickets/`.

## Supporting Foundations

- **[frontend-design](.gemini/skills/frontend-design/SKILL.md)**: Create distinctive, production-grade frontend interfaces with high design quality. - from https://github.com/anthropics/skills
- **[codebase-design](.gemini/skills/codebase-design/SKILL.md)**: Shared vocabulary for designing deep modules, seams, and testable interfaces - from https://github.com/mattpocock/skills
- **[write-great-skills](.gemini/skills/write-great-skills/SKILL.md)**: Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable - from https://github.com/mattpocock/skills
