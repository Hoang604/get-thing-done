---
name: gitnexus-pr-review
description: "Review pull requests, understand changes, and assess merge risk using GitNexus. Use when asked 'Review this PR', 'What does PR #42 change?', or 'Is this PR safe to merge?'."
---

# PR Review with GitNexus

Use this skill to perform a deep architectural review of pull requests by mapping code changes to affected execution flows and identifying potential breaking changes.

## Workflow

1. **Fetch PR Diff**: Use `gh pr diff <number>` or `git diff base...head` to get the raw changes.
2. **Map Changes to Flows**: Execute `gitnexus_detect_changes({scope: "compare", base_ref: "main"})` to identify affected execution flows and symbols.
3. **Analyze Impact per Symbol**: For each non-trivial changed symbol, run `gitnexus_impact({target: "<symbol>", direction: "upstream"})` to find its blast radius.
4. **Understand Role**: Use `gitnexus_context({name: "<key symbol>"})` to understand the symbol's role (callers, callees, and process participation).
5. **Check Affected Flows**: Read `gitnexus://repo/{name}/processes` to verify all affected execution flows are accounted for.
6. **Assess Risk & Coverage**: Check if affected processes have test coverage using `gitnexus_impact({includeTests: true})`.
7. **Summarize Findings**: Write a review summary with a risk assessment and specific findings.

## Risk Assessment

### Review Signals

| Signal | Risk Level |
| :--- | :--- |
| Changes touch <3 symbols, 0-1 processes. | **LOW** |
| Changes touch 3-10 symbols, 2-5 processes. | **MEDIUM** |
| Changes touch >10 symbols or many processes. | **HIGH** |
| Changes touch auth, payments, or data integrity code. | **CRITICAL** |
| **d=1** callers exist outside the PR diff. | **BREAKING CHANGE** — Flag it! |

## Checklist

- [ ] Fetch the PR diff.
- [ ] Run `gitnexus_detect_changes` to map changes to execution flows.
- [ ] Run `gitnexus_impact` on each non-trivial changed symbol.
- [ ] Review **d=1** items (WILL BREAK) — verify if all callers are updated in the PR.
- [ ] Run `gitnexus_context` on key changed symbols for a full picture.
- [ ] Verify if affected processes have adequate test coverage.
- [ ] Assess the overall risk level and write the review summary.

## Review Output Format

Structure your review as follows:

```markdown
## PR Review: <title>

**Risk: LOW / MEDIUM / HIGH / CRITICAL**

### Changes Summary
- <N> symbols changed across <M> files.
- <P> execution flows affected.

### Findings
1. **[severity]** Description of finding.
   - Evidence from GitNexus tools.
   - Affected callers/flows.

### Missing Coverage
- Callers not updated in PR: ...
- Untested flows: ...

### Recommendation
APPROVE / REQUEST CHANGES / NEEDS DISCUSSION
```

## Tools Reference

- **gitnexus_detect_changes**: Map PR diffs to affected execution flows and symbols.
- **gitnexus_impact**: Analyze blast radius and check for test coverage.
- **gitnexus_context**: Understand a changed symbol's role and relationships.
