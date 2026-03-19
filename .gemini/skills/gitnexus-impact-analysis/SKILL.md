---
name: gitnexus-impact-analysis
description: "Assess the blast radius and safety of code changes using GitNexus. Use when asked 'Is it safe to change X?', 'What depends on this?', or 'What will break?'."
---

# Impact Analysis with GitNexus

Use this skill to perform safety analysis before editing code or committing changes by identifying affected dependencies and execution flows.

## Workflow

1. **Analyze Upstream Impact**: Execute `gitnexus_impact({target: "X", direction: "upstream"})` to find what depends on the target symbol.
2. **Check Execution Flows**: Read `gitnexus://repo/{name}/processes` to identify which execution flows (processes) are affected by the change.
3. **Pre-Commit Check**: Run `gitnexus_detect_changes()` to map current git changes to affected flows and symbols.
4. **Assess Risk**: Evaluate the risk level based on the depth and number of affected items and report to the user.

## Risk Assessment

### Impact Depth

| Depth | Risk Level | Meaning |
| :--- | :--- | :--- |
| **d=1** | **WILL BREAK** | Direct callers or importers. |
| **d=2** | **LIKELY AFFECTED** | Indirect dependencies. |
| **d=3** | **MAY NEED TESTING** | Transitive effects. |

### Overall Risk Level

| Affected | Risk |
| :--- | :--- |
| <5 symbols, few processes | **LOW** |
| 5-15 symbols, 2-5 processes | **MEDIUM** |
| >15 symbols or many processes | **HIGH** |
| Critical path (e.g., auth, payments) | **CRITICAL** |

## Checklist

- [ ] Run `gitnexus_impact({target, direction: "upstream"})` to find dependents.
- [ ] Review **d=1** items first (these WILL BREAK).
- [ ] Check high-confidence (>0.8) dependencies.
- [ ] Read `processes` to check affected execution flows.
- [ ] Run `gitnexus_detect_changes()` for a pre-commit check.
- [ ] Assess the final risk level and report it to the user.

## Tools Reference

- **gitnexus_impact**: Primary tool for symbol blast radius (upstream/downstream).
- **gitnexus_detect_changes**: Git-diff based impact analysis for staged or unstaged changes.

## Example: "What breaks if I change validateUser?"

1. Run `gitnexus_impact({target: "validateUser", direction: "upstream"})`.
   - *Result*: d=1: `loginHandler`, `apiMiddleware` (WILL BREAK); d=2: `authRouter`, `sessionManager` (LIKELY AFFECTED).
2. Read `gitnexus://repo/my-app/processes`.
   - *Result*: `LoginFlow` and `TokenRefresh` participate in `validateUser`.
3. Final Assessment: 2 direct callers, 2 processes = **MEDIUM** risk.
