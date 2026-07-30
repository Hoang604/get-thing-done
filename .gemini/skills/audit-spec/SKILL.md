---
name: audit-spec
description: Adversarially audit a SPEC.md document to identify domain entropy, missing fallbacks, and contradictions.
disable-model-invocation: true
---

# CORE DIRECTIVE

Read the target `SPEC.md`. Act as an adversarial auditor. Hunt for `domain entropy` (missing invariants, unhandled edge cases, and dangling states). Restrict your output strictly to the audit report. Base all findings exclusively on text present in the document. Retain the target specification file exactly as written.

---

# PRIMARY TIER: ORDERED STEPS (`Immediate Action`)

## Step 1: Trace Execution Graphs (`Dangling State Hunt`)
Read every requirement in the specification. Trace every domain path and error fallback. For every clause (`When`, `While`, or `If`), verify that all domain entities used within it possess an explicit upstream definition, and that the clause results in a downstream exit condition.

## Step 2: Hunt Missing Fallbacks (`Error State Hunt`)
For every trigger or event where failure is physically or logically possible, verify an explicit fallback (`If X fails`) is defined. 

## Step 3: Check Invariant Violations (`Contradiction Hunt`)
Cross-reference every domain rule against stated product invariants. Identify any rule that violates a core invariant or creates a logical contradiction.

## Step 4: Hunt Unobservable States (`Vagueness Hunt`)
Scan all requirements for subjective adjectives, adverbs, or undefined thresholds (`e.g., "fast", "sometimes", "efficient", "large"`). Flag any rule that cannot be strictly `Black-Box Verified` by a machine or tester without subjective interpretation.

## Step 5: Output Audit Report (`Checkable Completion`)
Generate a numbered list of localized entropy points. Format exactly as:
`[Concept/Trigger] <Exact description of missing state, unhandled fallback, unobservable term, or conflict>`

If you find zero entropy points across all four vectors, output exactly:
`[ENTROPY: ZERO]`

**Halt.** Await the user's explicit resolution of the flagged entropy points.
