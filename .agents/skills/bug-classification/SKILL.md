---
name: bug-classification
description: Trace codebase problems across the three-tier causal chain to determine whether the true root cause stops at Layer 2 (LOCAL) or originates at Layer 3 (ARCHITECTURAL)
disable-model-invocation: true
---

# Root-Cause & Bug Classification

For every codebase problem in scope, establish the causal chain and determine whether the true root cause stops at **Layer 2 (`LOCAL`)** or originates at **Layer 3 (`ARCHITECTURAL`)**:

- **Layer 1 (Symptom)**: The surface issue observed in the codebase.
- **Layer 2 (Proximate / Local Cause)**: The concrete code (`file:line`) that directly produces Layer 1.
- **Layer 3 (Architectural Root Cause)**: The underlying design in the codebase that hindered writing clean code at Layer 2.

A problem's true root cause is:
- **`LOCAL` (stops at Layer 2)** when the surrounding design already provides everything needed to express the right behavior cleanly in place, so the fault is purely a local implementation mistake inside a sound design.
- **`ARCHITECTURAL` (originates at Layer 3)** when Layer 2 is itself the consequence of a design elsewhere in the codebase that hindered writing clean code at Layer 2, so patching Layer 2 alone leaves that design flaw in place.

---

## General Methodology

1. **Locate Layer 2 from Layer 1**: Find the exact `file:line` that directly produces the symptom.
2. **Question why Layer 2 took that form**: Ask why a clean implementation was not written there in the first place and what hinders writing the cleanest possible fix right at Layer 2.
3. **Trace the hindrance to its origin**: When clean code at Layer 2 is hindered by what surrounds it, follow the dependencies across the codebase (including through any intermediate layers in between) to the design boundary that holds the authority to remove that hindrance at its source (Layer 3).
4. **Prove every link with codebase evidence**: Back each tier in the causal chain with concrete `file:line` citations.

---

## Guiding Principle

No formula covers every way a design can obstruct clean code; rely on your judgment of the architecture. As a general lens: a sound design enforces invariants at the point of entry and defines boundaries so that everything outside a boundary has **less to know and less to change**. Whenever code at Layer 2 is forced to compensate for a responsibility that belongs to another boundary, the root cause lies in that boundary's design (Layer 3) rather than at the site forced to compensate (Layer 2).

---

## Deliverable

Present the analysis directly in the conversation (do not edit code or create files unless asked). Group problems into **`LOCAL` (Layer 2 Root Cause)** and **`ARCHITECTURAL` (Layer 3 Root Cause)**, and for each problem state:

```markdown
### [Problem Title] — Verdict: `LOCAL` (Layer 2) | `ARCHITECTURAL` (Layer 3)
- **Layer 1 (Symptom)**: [What surfaces in the codebase, with `file:line` if applicable]
- **Layer 2 (Local Cause)**: [`file:line` — the proximate code producing Layer 1 and what it currently does]
- **Layer 3 (Architectural Root Cause)**: [If `LOCAL`: state why the surrounding design is already sufficient. If `ARCHITECTURAL`: identify the originating design/boundary at `file:line`, any intermediate layers at `file:line` that propagate the constraint, and how that design obstructed clean code at Layer 2]
```
