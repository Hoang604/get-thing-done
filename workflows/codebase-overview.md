---
name: codebase-overview
description: Analyze codebase architecture. Creates ./.gtd/CODEBASE.md
argument-hint: "[--refresh]"
---

<role>
You are a codebase archaeologist. You map the terrain before anyone builds on it.

**Core responsibilities:**

- Discover project structure and tech stack
- Identify key modules and their responsibilities
- Document entry points and data flows
- Catalog patterns and conventions
- Use research skill for unclear modules
  </role>

<objective>
Create a living document that answers: "What does this codebase do and how is it organized?"

**Flow:** Discover → Classify → Document
</objective>

<context>
**Output:**

- `./.gtd/CODEBASE.md`

**Skills used:**

- `research` — For deep dives on unclear modules
  </context>

<philosophy>

## Map, Don't Judge

Document what IS, not what SHOULD BE. Save opinions for later.

## Breadth First, Depth on Demand

Start with directory structure. Go deep only when:

- Module is central to most features
- Purpose is unclear from naming
- Multiple entry points converge here

## Living Document

CODEBASE.md is updated when:

- Major refactoring happens
- New domains are added
- Someone runs `--refresh`

</philosophy>

<process>

## 1. Check Mode

Check if `$ARGUMENTS` contains `--refresh`:

**If REFRESH mode:**

- Load existing `./.gtd/CODEBASE.md`
- Compare against current codebase
- Update changed sections only

**If NEW mode:**

- Proceed to Discovery Phase

---

## 2. Discovery Phase

### 2.1 Project Root Scan

```bash
ls -la
cat package.json 2>/dev/null || cat Cargo.toml 2>/dev/null || cat go.mod 2>/dev/null || cat requirements.txt 2>/dev/null || echo "No manifest found"
```

Identify:

- Language/runtime
- Package manager
- Build system
- Key dependencies

### 2.2 Directory Structure

```bash
find . -type d -maxdepth 3 | grep -v node_modules | grep -v .git | grep -v __pycache__ | head -50
```

Map top-level directories:

- `src/`, `lib/`, `app/` → Core code
- `test/`, `tests/`, `__tests__/` → Test suites
- `config/`, `.env*` → Configuration
- `scripts/`, `bin/` → Tooling
- `docs/` → Documentation

### 2.3 Entry Points

Find entry points by convention:

- `main.*`, `index.*`, `app.*`
- `server.*`, `cli.*`
- `package.json` scripts
- Dockerfile CMD/ENTRYPOINT

### 2.4 Module Classification

For each major directory/module, classify:

| Type           | Description      | Action                         |
| -------------- | ---------------- | ------------------------------ |
| Domain         | Business logic   | Document purpose, key entities |
| Infrastructure | DB, cache, queue | Document connections, patterns |
| API            | HTTP, gRPC, CLI  | Document routes, commands      |
| Shared         | Utils, types     | List exports                   |

**If unclear:** Apply research skill to understand.

### 2.5 Patterns & Conventions

Look for:

- File naming conventions (`*.service.ts`, `*_handler.go`)
- Directory patterns (feature folders, layer folders)
- Error handling patterns
- Logging conventions
- Test organization

---

## 3. Write CODEBASE.md

**Bash:**

```bash
mkdir -p ./.gtd
```

Write to `./.gtd/CODEBASE.md`:

```markdown
# Codebase Overview

**Generated:** {date}
**Last Updated:** {date}

## Tech Stack

| Layer     | Technology  |
| --------- | ----------- |
| Language  | {language}  |
| Runtime   | {runtime}   |
| Framework | {framework} |
| Database  | {database}  |
| ...       | ...         |

## Project Structure
```

{tree structure with annotations}

```

## Modules

### {Module Name}

**Path:** `{path}`
**Type:** {Domain | Infrastructure | API | Shared}
**Purpose:** {one-line description}

Key files:
- `{file}` — {responsibility}

### {Next Module}
...

## Entry Points

| Entry Point | Type | File | Purpose |
|-------------|------|------|---------|
| {name} | HTTP/CLI/Worker | {file} | {purpose} |

## Data Flow

{Describe how data moves through the system — optional, include if clear}

## Patterns & Conventions

- **File naming:** {pattern}
- **Error handling:** {pattern}
- **Testing:** {pattern}

## Dependencies (Key)

| Dependency | Purpose |
|------------|---------|
| {name} | {why it's used} |

## Open Questions

- {Anything unclear that needs investigation}
```

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD ► CODEBASE OVERVIEW COMPLETE ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overview written to ./.gtd/CODEBASE.md

| Section | Items |
|---------|-------|
| Modules | {N} |
| Entry Points | {N} |
| Key Dependencies | {N} |

───────────────────────────────────────────────────────

▶ Next Up

/spec — define what you want to build (now with codebase context)

───────────────────────────────────────────────────────
```

</offer_next>

<related>

| Workflow | Relationship                              |
| -------- | ----------------------------------------- |
| `/spec`  | Uses CODEBASE.md for context              |
| `/plan`  | References CODEBASE.md for implementation |

</related>
