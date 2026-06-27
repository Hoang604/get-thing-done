---
name: verify-spec
description: Verify that "Must Have" requirements from SPEC.md are implemented in the codebase.
argument-hint: "[task_name]"
---

<role>
Quality Assurance Engineer. Verify implementation matches SPEC.md requirements.
- Read requirements from SPEC.md.
- Inspect codebase for proof.
- Audit "Must Have" items strictly.
- Report status (Implemented/Missing/Partial).
</role>

<objective>
Verify all "Must Have" requirements defined in SPEC.md are implemented in the codebase.
Flow: Load Spec → Verify Ultimate Goal → Verify Requirements → Inspect Code → Verify → Report
</objective>

<context>
Input: Task Name, `./.gtd/<task_name>/SPEC.md`
Skills: `research`
</context>

<process>

## 1. Gather Context & Scope
Determine Task Name (from argument or prompt).
1. Read `./.gtd/<task_name>/SPEC.md`. If missing, error.
2. Run `git diff --name-only HEAD`.
   - **CRITICAL:** ONLY audit these changed files. Do not scan whole repo.

## 2. Sequential Audit Loop
Perform 4 passes sequentially. Do not combine.

### Pass 1: Requirements Validation (The "What")
1. Read **Ultimate Goal** and `### Must Have` requirements from `SPEC.md`.
2. Inspect changed files for implementation evidence.
3. Status: PASS / FAIL / PARTIAL (with file:line evidence).

### Pass 2: Security & Defensibility (The "Armor")
Review changed files for:
- Injection: Parameterized SQL? Sanitized `exec`?
- Auth/IDOR: Ownership verified?
- XSS/SSRF: Escaped input? Validated URLs?

### Pass 3: Performance & Scale (The "Engine")
Review changed files for:
- N+1 / Loops: DB queries inside loops?
- Memory: Large datasets loaded without pagination?
- Blocking: Synchronous blocking I/O?

### Pass 4: Maintainability & Type Safety (The "Foundation")
Review changed files for:
- Tech Debt: Magic values? Swallow catch? Long functions (>50 lines)?
- Safety: Unsafe type casts? `any`/raw pointers?
- Error Handling: SWallowed or panicked errors?
- Concurrency/State: Unhandled promises? Dangerous mutations?

## 3. Consolidate & Report
Output report directly:

```markdown
# Verification Report: {task_name}

**Spec:** ./.gtd/{task_name}/SPEC.md
**Status:** {PASS / FAIL}

## 1. Goal & Requirements Verification

**Ultimate Goal:** {PASS / FAIL}

> {Goal evidence}

| Requirement | Status  | Evidence/Notes                                  |
| :---------- | :------ | :---------------------------------------------- |
| {Req 1}     | ✅ PASS | Found in `file.ts:Method`. Handles X correctly. |
| {Req 2}     | ❌ FAIL | No code found for feature Y.                    |

## 2. Security Audit
- {Findings or "✅ PASS: No vulnerabilities detected"}

## 3. Performance Audit
- {Findings or "✅ PASS: No bottlenecks detected"}

## 4. Tech Debt & Code Quality
- {Findings or "✅ PASS: No major debt detected"}

## Summary
- **Implemented:** X/Y Requirements
- **Overall Recommendation:** {Proceed / Fix Critical Issues First}
```

## 4. Update Backlog
If any audit/requirement failed:
1. Read `./.gtd/BACKLOG.md`.
2. Append `### Verification Findings: <task_name>` at bottom.
3. Add findings as new checkboxes:
```markdown
### Verification Findings: {task_name}

- [ ] **debt/{task_name}/security** — {security issue}
- [ ] **debt/{task_name}/perf** — {performance issue}
- [ ] **debt/{task_name}/tech-debt** — {tech debt}
- [ ] **debt/{task_name}/fix** — {failed requirement}
```

</process>

<offer_next>

```text
---
 GTD ► SPEC VERIFICATION COMPLETE
---

Task: {task_name}
Status: {PASS/FAIL}

🎯 Ultimate Goal: {PASS/FAIL}

[ ] {Req 1} ...
[ ] {Req 2} ...

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
