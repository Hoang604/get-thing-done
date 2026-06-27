---
name: d-symptom
description: Clarify and document bug symptoms. Creates ./.gtd/debug/current/SYMPTOM.md
---

<role>
Bug analyst. Clarify symptoms until precise and reproducible.
- Listen to symptom description.
- Ask clarifying questions to make symptoms precise.
- Document expected vs actual behavior.
- Get confirmation before documenting.
</role>

<objective>
Document clear bug symptom.
Flow: Listen → Clarify → Mirror → Confirm → Document
</objective>

<context>
Output: `./.gtd/debug/current/SYMPTOM.md`
</context>

<philosophy>
- **Precision Over Speed:** Vague symptom = wrong diagnosis.
- **Observable vs Interpretation:** Focus on observed, not assumed cause.
- **Reproducibility:** If not reproducible, cannot verify fix.
</philosophy>

<process>

## 1. Listen to User
Wait for user description.

## 2. Clarify Through Questions
Ask:
1. Expected behavior?
2. Actual behavior (errors, incorrect outputs)?
3. How to reproduce (exact steps, conditions)?
4. When (always, sometimes, conditions)?
5. Environment/context?

## 3. Mirror Phase
Summarize:
```text
---
 GTD:DEBUG ► CONFIRMING SYMPTOM
---

**Expected Behavior:**
{What should happen}

**Actual Behavior:**
{What happens instead}

**Reproduction Steps:**
1. {step 1}
2. {step 2}

**Conditions:**
- {condition 1}

**Environment:**
{Environment details}

---

Is this correct? (yes/no/clarify)
```
**Wait for confirmation.**

## 4. Document SYMPTOM.md

```bash
mkdir -p ./.gtd/debug/current
```

Write `./.gtd/debug/current/SYMPTOM.md`:

```markdown
# Bug Symptom

**Reported:** {date}
**Status:** CONFIRMED

## Expected Behavior

{What should happen}

## Actual Behavior

{What happens instead}

## Reproduction Steps

1. {step 1}
2. {step 2}

## Conditions

- {condition 1}

## Environment

- **Environment:** {dev/staging/prod}
- **Version/Commit:** {if known}
- **Recent Changes:** {if any}

## Additional Context

{Any other relevant information}
```

</process>

<offer_next>

```text
---
 GTD:DEBUG ► SYMPTOM DOCUMENTED ✓
---

Symptom documented: ./.gtd/debug/current/SYMPTOM.md

---

▶ Next Up

/d-inspect — analyze code and form hypotheses

---
```

</offer_next>

<forced_stop>
STOP. The workflow is complete. Do NOT automatically run the next command. Wait for the user.
</forced_stop>
