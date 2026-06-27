---
name: d-inspect
description: Inspect code and propose root cause hypotheses. Creates ./.gtd/debug/current/HYPOTHESES.md
---

<role>
Code investigator. Analyze code to form hypotheses about root causes.
- Read symptom description.
- Inspect relevant code paths.
- Form multiple hypotheses ranked by confidence.
- Document reasoning for each hypothesis.
</role>

<objective>
Generate ranked hypotheses about root cause of bug.
Flow: Load Symptom → Trace Code → Form Hypotheses → Rank by Confidence
</objective>

<context>
Required: `./.gtd/debug/current/SYMPTOM.md`
Output: `./.gtd/debug/current/HYPOTHESES.md`
Skills: `research`
</context>

<philosophy>
- **Multiple Hypotheses:** Generate 3-5 competing hypotheses.
- **Confidence Scoring:** High (70-90%), Medium (40-70%), Low (10-40%).
- **Evidence-Based:** Must analyze code to support hypotheses.
</philosophy>

<process>

## 1. Load Symptom

Read `./.gtd/debug/current/SYMPTOM.md`.

```bash
if ! ls "./.gtd/debug/current/SYMPTOM.md" >/dev/null 2>&1; then
    echo "Error: No symptom documented. Run /d-symptom first."
    exit 1
fi
```

---

## 2. Trace Code Paths
1. **Entry points:** which triggers symptom?
2. **Execution flow:** trace branches, conditions, errors.
3. **Suspect areas:** recent changes, complex logic, state, deps.
4. **Related files:** config, DB, deps.

---

## 3. Form Hypotheses
Each hypothesis needs: Description, Evidence (code observations), Verification method, Confidence %.
**Generate 3-5 hypotheses ranked most to least likely.**

---

## 4. Document HYPOTHESES.md

Write `./.gtd/debug/current/HYPOTHESES.md`:

```markdown
# Root Cause Hypotheses

**Analyzed:** {date}
**Status:** PENDING VERIFICATION

## Summary

Based on code analysis, here are the most likely root causes:

---

## Hypothesis 1: {Short description}

**Confidence:** High (75%)

**Description:**
{Detailed explanation of what you think is wrong}

**Evidence:**

- {Observation 1 from code}
- {Observation 2 from code}
- {Supporting fact}

**Location:**

- Files: `{file1}`, `{file2}`
- Lines: {line ranges}

**Verification Method:**
{How to confirm/reject this hypothesis}

---

## Hypothesis 2: {Short description}

**Confidence:** Medium (50%)

{Same structure as above}

---

## Hypothesis 3: {Short description}

**Confidence:** Low (25%)

{Same structure as above}

---

## Code Analysis Notes

{Any additional observations, patterns, or concerns}
```

</process>

<offer_next>

```text
---
  GTD:DEBUG ► HYPOTHESES GENERATED ✓
---

Hypotheses documented: ./.gtd/debug/current/HYPOTHESES.md

Total hypotheses: {N}
Highest confidence: {X}%

---

▶ Next Up

/d-verify — verify hypotheses with debug logs

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
