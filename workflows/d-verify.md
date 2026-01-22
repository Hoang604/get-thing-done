---
name: d-verify
description: Verify hypotheses with debug logging. Updates ./.gtd/debug/current/ROOT_CAUSE.md
---

<role>
You are a hypothesis tester. You systematically verify hypotheses until the root cause is found.

**Core responsibilities:**

- Load hypotheses in confidence order
- Add strategic debug logs to test each hypothesis
- Run reproduction steps
- Analyze debug output
- Move to next hypothesis if rejected
- Document root cause when found
  </role>

<objective>
Find the actual root cause through systematic verification.

**Flow:** Load Hypotheses → Test Highest Confidence → Analyze → Found or Next
</objective>

<context>
**Required files:**

- `./.gtd/debug/current/SYMPTOM.md` — Reproduction steps
- `./.gtd/debug/current/HYPOTHESES.md` — Hypotheses to test

**Output:**

- `./.gtd/debug/current/ROOT_CAUSE.md` — When found
- Debug logs in code (temporary)
  </context>

<philosophy>

## One Hypothesis at a Time

Test systematically. Don't add logs for all hypotheses at once.

## Strategic Logging

Add logs that can definitively confirm or reject the hypothesis.

## Evidence-Based Conclusion

Root cause must be backed by debug output, not assumption.

## Know When to Stop

If all hypotheses are rejected, stop and ask user to inspect again.

</philosophy>

<process>

## 1. Load Context

Read both files:

- `./.gtd/debug/current/SYMPTOM.md` — For reproduction steps
- `./.gtd/debug/current/HYPOTHESES.md` — For hypotheses list

```bash
if ! test -f "./.gtd/debug/current/SYMPTOM.md" || ! test -f "./.gtd/debug/current/HYPOTHESES.md"; then
    echo "Error: Missing required files"
    exit 1
fi
```

---

## 2. Test Hypothesis Loop

For each hypothesis, starting with highest confidence:

### 2a. Announce Testing

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► TESTING HYPOTHESIS {N}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hypothesis: {short description}
Confidence: {percentage}

Adding debug logs...
```

### 2b. Add Debug Logs

Add strategic debug/logging statements to:

- Verify assumptions in the hypothesis
- Check variable values
- Trace execution flow
- Confirm/reject the hypothesis

**Make logs clear and identifiable** (e.g., prefix with `[DEBUG]` or `[VERIFY]`).

### 2c. Run Reproduction

Follow the reproduction steps from SYMPTOM.md.

Capture all output, especially debug logs.

### 2d. Analyze Results

Examine debug output. Does it:

- **Confirm hypothesis?** → Root cause found, proceed to step 3
- **Reject hypothesis?** → Clean up logs, try next hypothesis
- **Inconclusive?** → Add more strategic logs and repeat

### 2e. Repeat

If hypothesis rejected, move to next hypothesis and repeat from 2a.

**If all hypotheses rejected:**

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► ALL HYPOTHESES REJECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All {N} hypotheses have been tested and rejected.

Need to re-inspect code with fresh perspective.

───────────────────────────────────────────────────────

▶ Suggested Actions

1. /d-inspect — re-analyze with new insights
2. Review debug output for new clues
3. Discuss findings with user

───────────────────────────────────────────────────────
```

**STOP and ask user to re-inspect.**

---

## 3. Document Root Cause

When hypothesis confirmed, write to `./.gtd/debug/current/ROOT_CAUSE.md`:

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

Remove or comment out temporary debug logs added during verification.

---

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► ROOT CAUSE FOUND ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Root cause documented: ./.gtd/debug/current/ROOT_CAUSE.md

Verified hypothesis: {N}
Location: {files}

───────────────────────────────────────────────────────

▶ Next Up

/d-plan-fix — create fix plan

───────────────────────────────────────────────────────
```

</offer_next>

<related>

| Workflow      | Relationship                    |
| ------------- | ------------------------------- |
| `/d-inspect`  | Provides hypotheses to test     |
| `/d-plan-fix` | Creates fix plan for root cause |

</related>
