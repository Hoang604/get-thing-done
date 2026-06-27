---
name: codebase-overview
description: Analyze codebase architecture. Creates ./.gtd/CODEBASE.md and split docs under ./.gtd/codebase/
argument-hint: "[--refresh]"
---

<role>
Codebase archaeologist. Maps terrain before building.
- Discover structure, tech stack.
- Identify domains, infra, entry points.
- Document flows, conventions.
- Create split docs.
- Use research skill.
</role>

<objective>
Create living codebase map: what it does, organization, where to inspect.
Flow: Discover → Classify → Split → Document
</objective>

<context>
Outputs:
- `./.gtd/CODEBASE.md` (thin index)
- `./.gtd/codebase/architecture.md`
- `./.gtd/codebase/entrypoints.md`
- `./.gtd/codebase/patterns.md`
- `./.gtd/codebase/open-questions.md`
- `./.gtd/codebase/domains/index.md`
- `./.gtd/codebase/domains/*.md`
- `./.gtd/codebase/infra/index.md`
- `./.gtd/codebase/infra/*.md`
</context>

<philosophy>
- **Map, Don't Judge:** Document what IS. No opinions.
- **Split early:** CODEBASE.md thin. Use targeted docs.
- **Breadth first:** Core details, deep dive on demand.
- **Living:** Each file needs `Generated`, `Last Updated`, `Last Verified`.
</philosophy>

<prohibitions>
- **No Name Guessing:** Do not describe module by name alone. Read code.
- **Evidence Required:** Cite paths/lines inline (`Evidence: path/to/file:line`). No citation = no write.
- **Admit Unknowns:** Log to `open-questions.md`.
</prohibitions>

<process>

## 1. Check Mode

Check `$ARGUMENTS` for `--refresh`.

**If REFRESH mode:**
- Load `./.gtd/CODEBASE.md` and `./.gtd/codebase/` files.
- Revalidate sections against codebase.
- Update stale files. Create missing split docs.

**If NEW mode:**
- Go to Discovery.

---

## 2. Discovery Phase

### 2.1 Project Root Scan

```bash
ls -la
cat package.json 2>/dev/null || cat Cargo.toml 2>/dev/null || cat go.mod 2>/dev/null || cat requirements.txt 2>/dev/null || echo "No manifest found"
```

Identify: Language/runtime, package manager, build system, dependencies.

### 2.2 Directory Structure

```bash
find . -type d -maxdepth 3 | grep -v node_modules | grep -v .git | grep -v __pycache__ | head -80
```

Classify directories: Domain, Infra, API/interface, Shared, Tests, Tooling.

### 2.3 Entry Points

Find entry points by convention and wiring:
- `main.*`, `index.*`, `app.*`
- `server.*`, `cli.*`, workers, package scripts, Dockerfile, framework configs.

### 2.4 Module Classification

Classify each directory:

| Type | Description | Output |
| ---- | ----------- | ------ |
| Domain | Business logic or core product concepts | `domains/<name>.md` |
| Infrastructure | DB, cache, queue, external services, persistence | `infra/<name>.md` |
| API | HTTP, CLI, RPC, workers, public integration points | `entrypoints.md` or subsystem doc |
| Shared | Types, utilities, common libraries | `architecture.md` or a focused doc if central |

### 2.5 Patterns & Conventions

Look for patterns: Naming, layering, error handling, logging, testing, wrappers. Evidence in at least two files.

---

## 3. Create Split Documentation

```bash
mkdir -p ./.gtd/codebase/domains ./.gtd/codebase/infra ./.gtd/scripts
```

### 3.1 Setup Index Generator

Create `./.gtd/scripts/generate-index.sh`:
1. Accepts target directory.
2. Creates/overwrites `index.md`.
3. For every `.md` file (except `index.md` itself), appends:
   - `<!-- Imported from: ./{filename} -->`
   - File content
   - `<!-- End of import from: ./{filename} -->`

### 3.2 Write `./.gtd/CODEBASE.md`

Thin index only. Required structure:

```markdown
# Codebase Index

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

## Purpose

- One short paragraph summarizing the codebase.
- Include `Evidence: ...`

## Documentation Map

- [Architecture](./codebase/architecture.md) — overall structure and major subsystems
- [Entrypoints](./codebase/entrypoints.md) — application boot paths, commands, servers, workers
- [Patterns](./codebase/patterns.md) — verified conventions used across files
- [Open Questions](./codebase/open-questions.md) — unresolved items requiring later investigation

## Domain Docs

- [Domain: {name}](./codebase/domains/{name}.md) — one-line purpose

## Infrastructure Docs

- [Infra: {name}](./codebase/infra/{name}.md) — one-line purpose
```

### 3.1.1 Write directory indexes

Run script:

```bash
bash ./.gtd/scripts/generate-index.sh ./.gtd/codebase/domains
bash ./.gtd/scripts/generate-index.sh ./.gtd/codebase/infra
```

### 3.2 Write `./.gtd/codebase/architecture.md`

Required structure:

```markdown
# Architecture

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

## Tech Stack

| Layer | Technology | Evidence |
| ----- | ---------- | -------- |
| Language | {value} | {path:line} |
| Runtime | {value} | {path:line} |
| Framework | {value} | {path:line} |

## Project Structure

{annotated tree or concise list}

Evidence: {paths and lines used}

## Major Subsystems

### {Subsystem Name}

- Type: {Domain | Infrastructure | API | Shared}
- Path: `{path}`
- Purpose: {verified sentence}
- Depends on: {verified dependencies}
- Used by: {verified callers or consumers}
- Evidence: {path:line, path:line}
```

### 3.3 Write `./.gtd/codebase/entrypoints.md`

Required structure:

```markdown
# Entrypoints

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

| Entrypoint | Type | File | Purpose | Evidence |
| ---------- | ---- | ---- | ------- | -------- |
| {name} | HTTP/CLI/Worker/Test/Script | `{file}` | {verified purpose} | {path:line} |

## Startup Flows

### {Flow Name}

1. {step}
2. {step}

Evidence: {path:line, path:line}
```

### 3.4 Write `./.gtd/codebase/patterns.md`

Required structure:

```markdown
# Patterns And Conventions

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

## Verified Patterns

### {Pattern Name}

- Description: {verified description}
- Why it appears to exist: {brief observation only if evidence supports it}
- Examples: `{path}`, `{path}`
- Evidence: {path:line, path:line}
```

### 3.5 Write `./.gtd/codebase/open-questions.md`

Required structure:

```markdown
# Open Questions

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

- {question}
  - Why unresolved: {brief reason}
  - Next place to inspect: `{path}` if known
```

### 3.6 Write domain and infrastructure docs

Create focused file per area.

Domain doc template:

```markdown
# Domain: {Name}

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

## Purpose

{verified summary}

Evidence: {path:line, path:line}

## Key Files

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `{file}` | {verified responsibility} | {path:line} |

## Important Flows

### {Flow Name}

1. {step}
2. {step}

Evidence: {path:line, path:line}

## Dependencies

- `{dependency/module}` — {verified relationship}. Evidence: {path:line}
```

Infrastructure doc template:

```markdown
# Infrastructure: {Name}

**Generated:** {date}
**Last Updated:** {date}
**Last Verified:** {date}

## Purpose

{verified summary}

Evidence: {path:line, path:line}

## Interfaces

| File | Responsibility | Evidence |
| ---- | -------------- | -------- |
| `{file}` | {verified responsibility} | {path:line} |

## Integration Points

- `{caller or consumer}` — {verified connection}. Evidence: {path:line}

## Operational Notes

- Only include if directly supported by code or config.
- Each note must end with `Evidence: {path:line}`
```

---

## 4. Refresh Rules

On refresh:
- Revalidate `Last Verified` for files inspected.
- Update only changed/rechecked files.
- Remove stale claims.
- Add new split docs. Keep `CODEBASE.md` concise.

</process>

<offer_next>

```text
---
  GTD ► CODEBASE OVERVIEW COMPLETE ✓
---

Index written to ./.gtd/CODEBASE.md
Split docs written to ./.gtd/codebase/

| File Group | Items |
|------------|-------|
| Domain Docs | {N} |
| Infra Docs | {N} |
| Shared Docs | {N} |

---

▶ Next Up

/spec — define what you want to build with codebase context available

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
