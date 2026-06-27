---
name: d-verify
description: Verify hypotheses with debug logging. Updates ./.gtd/debug/current/ROOT_CAUSE.md
---

<role>
Hypothesis tester. Systematically verify hypotheses until root cause is found.
- Load hypotheses in confidence order.
- Add strategic debug logs to test each hypothesis.
- Run reproduction steps.
- Analyze debug output.
- Move to next hypothesis if rejected.
- Document root cause when found.
</role>

<objective>
Find actual root cause through systematic verification.
Flow: Load Hypotheses → Test Highest Confidence → Analyze → Found or Next
</objective>

<context>
Required: `./.gtd/debug/current/SYMPTOM.md`, `./.gtd/debug/current/HYPOTHESES.md`
Output: `./.gtd/debug/current/ROOT_CAUSE.md` (when found), debug logs in code.
</context>

<philosophy>
- **One at a Time:** Test systematically.
- **Strategic Logging:** Definitive confirm/reject logs.
- **Evidence-Based:** conclusions backed by output.
- **Know When to Stop:** If all rejected, stop and discuss.
</philosophy>

<process>

## 1. Load Context

Read `SYMPTOM.md` and `HYPOTHESES.md`.

```bash
if ! ls "./.gtd/debug/current/SYMPTOM.md" >/dev/null 2>&1 || ! ls "./.gtd/debug/current/HYPOTHESES.md" >/dev/null 2>&1; then
    echo "Error: Missing required files"
    exit 1
fi
```

---

## 2. Test Hypothesis Loop
For each hypothesis, starting with highest confidence:

### 2a. Announce Testing
```text
---
 GTD:DEBUG ► TESTING HYPOTHESIS {N}
---

Hypothesis: {short description}
Confidence: {percentage}

Adding debug logs...
```

### 2b. Add Debug Logs
Add strategic debug statements (`[DEBUG]` or `[VERIFY]`) to trace flow, check values, verify assumptions.

### 2c. Run Reproduction
Follow reproduction steps from `SYMPTOM.md`. Capture output.

### 2d. Analyze Results
Examine debug output:
- **Confirm?** → Root cause found, go to step 3.
- **Reject?** → Clean up logs, try next hypothesis.
- **Inconclusive?** → Add more logs, repeat.

### 2e. Repeat
If rejected, try next. If all rejected:
```text
---
 GTD:DEBUG ► ALL HYPOTHESES REJECTED
---

All {N} hypotheses tested and rejected. Need fresh perspective.

---
▶ Suggested Actions
1. /d-inspect — re-analyze
2. Review debug output
3. Discuss with user
---
```
**STOP and ask user.**

---

## 3. Document Root Cause
When hypothesis confirmed, write `./.gtd/debug/current/ROOT_CAUSE.md`:

```markdown
# Root Cause

**Found:** {date}
**Status:** CONFIRMED

## Root Cause

{Clear description of the actual root cause}

## Verified Hypothesis

**Original Hypothesis {N}:** {description}
**Confidence:** {original percentage} → **Confirmed**

## Evidence

{Debug output and observations that confirmed this}

**Debug logs showed:**

- {key finding 1}
- {key finding 2}

## Location

- **Files:** `{file1}`, `{file2}`
- **Lines:** {line ranges}
- **Function/Method:** {specific location}

## Why It Causes The Symptom

{Explain the causal chain from root cause to observed symptom}

## Rejected Hypotheses

{List other hypotheses tested and why they were rejected}
```

### 3a. Clean Up Debug Logs
Remove temporary debug logs from code.

</process>

<offer_next>

```text
---
 GTD:DEBUG ► ROOT CAUSE FOUND ✓
---

Root cause documented: ./.gtd/debug/current/ROOT_CAUSE.md

Verified hypothesis: {N}
Location: {files}

---

▶ Next Up

/d-plan-fix — create fix plan

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
