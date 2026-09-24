---
name: classify-task
description: Diagnose task scope and blast radius by evaluating boundary caller invalidation
disable-model-invocation: true
---

# CORE DIRECTIVE

Inspect the codebase to determine the structural blast radius of the requested change.
Ground diagnosis exclusively in **Caller Invalidation** across touched boundaries. Do not propose workflows or draft implementation plans. Output the structural diagnosis block, then halt execution.

---

## 1. The Generative Boundary Principle

Evaluate the change against the primary boundary it touches:

- **Contract-Preserving**: The change satisfies or extends boundaries without invalidating existing caller guarantees. Dependents remain functional without mandatory interface adaptation.
- **Contract-Breaking**: The change alters structural invariants, invalidating established caller guarantees. Dependents cannot compile or execute without explicit adaptation, mandating topological inside-out propagation.

---

## 2. Structural Diagnosis Contract

Output the diagnosis strictly in this format:

```markdown
### Structural Task Diagnosis

- **Target Boundary**: [<file>](file:///path) (The primary interface, schema, or seam evaluated)
- **Caller Invalidation**: `Contract-Preserving` | `Contract-Breaking`
- **Blast Direction**: Topological propagation path from the touched boundary across its dependent call graph.
- **Invariant Delta**: Concrete structural difference between previous and target contract guarantees.
```

Output the diagnosis block and wait for user's next request.
