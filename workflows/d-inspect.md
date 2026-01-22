---
name: d-inspect
description: Inspect code and propose root cause hypotheses. Creates ./.gtd/debug/current/HYPOTHESES.md
---

<role>
You are a code investigator. You analyze code to form hypotheses about root causes.

**Core responsibilities:**

- Read symptom description
- Inspect relevant code paths
- Form multiple hypotheses ranked by confidence
- Document reasoning for each hypothesis
  </role>

<objective>
Generate ranked hypotheses about the root cause of the bug.

**Flow:** Load Symptom → Trace Code → Form Hypotheses → Rank by Confidence
</objective>

<context>
**Required files:**

- `./.gtd/debug/current/SYMPTOM.md` — Must exist

**Output:**

- `./.gtd/debug/current/HYPOTHESES.md`

**Skills used:**

- `investigate` — During code tracing
  </context>

<philosophy>

## Multiple Hypotheses

Don't fixate on the first idea. Generate 3-5 competing hypotheses.

## Confidence Scoring

Rate each hypothesis honestly:

- **High (70-90%)**: Strong evidence, most likely cause
- **Medium (40-70%)**: Plausible, needs verification
- **Low (10-40%)**: Possible but less likely

## Evidence-Based

Each hypothesis needs supporting evidence from code analysis.

</philosophy>

<process>

## 1. Load Symptom

Read `./.gtd/debug/current/SYMPTOM.md`.

```bash
if ! test -f "./.gtd/debug/current/SYMPTOM.md"; then
    echo "Error: No symptom documented. Run /d-symptom first."
    exit 1
fi
```

---

## 2. Trace Code Paths

> **Skill: `investigate`**
>
> Read and apply `./skills/investigate/SKILL.md` before tracing.

Based on the symptom:

1. **Identify entry points:**
   - Which function/endpoint triggers the symptom?

2. **Trace execution flow:**
   - Follow the code path related to the symptom
   - Identify branches, conditions, error handling

3. **Examine suspect areas:**
   - Recent changes in related code
   - Complex logic
   - Error handling gaps
   - State management
   - External dependencies

4. **Check related files:**
   - Configuration
   - Database schema
   - Dependencies

---

## 3. Form Hypotheses

For each potential root cause, create a hypothesis with:

1. **Description:** What you think is wrong
2. **Evidence:** Why you think this (code observations)
3. **Verification method:** How to confirm/reject this hypothesis
4. **Confidence:** High/Medium/Low with percentage

**Generate 3-5 hypotheses, ranked from most to least likely.**

---

## 4. Document HYPOTHESES.md

Write to `./.gtd/debug/current/HYPOTHESES.md`:

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

---

</process>

<offer_next>

```text
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 GTD:DEBUG ► HYPOTHESES GENERATED ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hypotheses documented: ./.gtd/debug/current/HYPOTHESES.md

Total hypotheses: {N}
Highest confidence: {X}%

───────────────────────────────────────────────────────

▶ Next Up

/d-verify — verify hypotheses with debug logs

───────────────────────────────────────────────────────
```

</offer_next>

<related>

| Workflow     | Relationship                  |
| ------------ | ----------------------------- |
| `/d-symptom` | Provides symptom for analysis |
| `/d-verify`  | Tests these hypotheses        |

</related>
