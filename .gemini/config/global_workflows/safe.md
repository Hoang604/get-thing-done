---
name: safe
description: Safeguard execution for costly or irreversible operations, speculative domain mutations, and semantic git conflicts by presenting rationale, blast radius, assumptions, and contingency before proceeding.
disable-model-invocation: true
---

# Safe Protocol

A safeguard protocol triggered prior to executing operations with high **Rollback Cost**, irreversible side effects, unverified domain assumptions, or semantic conflicts.

## Trigger Classes

1. **Destructive / Irreversible Operations**: Schema drop, branch force-push, bulk data mutation, production configuration changes, file deletion/overwrite without backup.
2. **Speculative Domain Mutation**: Writing business logic when requirements are ambiguous, unverified, or missing from codebase and documentation.
3. **Semantic Git Conflict**: Merging or resolving conflicts where competing branches implement divergent domain rules or intent.

## Information Hierarchy

### 1. Classify Rollback Cost & Blast Radius
Evaluate the operation against state persistence and domain integrity:
- **Rollback Cost**:
  - `Low`: Trivial local undo (`git checkout`, `git merge --abort`).
  - `High`: Complex recovery (reconstructing historical state, multi-service rollback, fixing corrupted business records).
  - `Irreversible`: Permanent data loss, remote history overwrite (`git push --force`), external API side effects.
- **Blast Radius**: Itemize all impacted files, entities, downstream services, and domain invariants.

*Completion Criterion*: Every target entity, side effect, and recovery classification is explicitly enumerated.

### 2. Formulate Rationale & Identify Assumptions
Clarify the necessity and surface latent uncertainty:
- **Justification**: Problem addressed and why this action is the selected path.
- **Alternatives Considered**: Why lower-risk or non-destructive approaches were rejected.
- **Unverified Assumptions**: If handling ambiguous domain rules, declare every unverified assumption and the risk if false.
- **Semantic Conflict Breakdown** (if resolving Git conflict):
  - *Ours Intent*: Domain rule and behavior of local branch.
  - *Theirs Intent*: Domain rule and behavior of incoming branch.
  - *Divergence*: Specific point of business logic collision.

*Completion Criterion*: Causal link established, alternatives evaluated, and all assumptions/divergences explicitly detailed.

### 3. Define Contingency
Establish the recovery or abort procedure:
- **Step-by-Step Rollback**: Exact commands or workflow to restore previous state (`git merge --abort`, backup restore script, migration rollback).
- **Irreversibility Declaration**: When no automated rollback exists, explicitly declare: "No automated rollback possible; recovery requires [manual procedure / backup restore / none]".

*Completion Criterion*: Verifiable recovery procedure documented or absence of rollback explicitly declared.

### 4. Hard Gate Halt
Output the structured report to the user and immediately halt execution without calling mutation tools.

Output format:
```markdown
### 🛡️ Safe Guard: [Action Summary]

- **Trigger Class**: [Destructive / Irreversible | Speculative Domain Mutation | Semantic Git Conflict]
- **Rollback Cost**: [Low | High | Irreversible]
- **Target / Blast Radius**:
  - [Target 1]: [Direct impact]
  - [Target 2]: [Downstream / domain invariant impact]
- **Rationale**:
  - [Why this action is necessary]
  - [Why lower-risk alternatives were not chosen]
- **Unverified Assumptions / Domain Divergence** (if applicable):
  - [Assumption / Conflict point 1]
- **Contingency / Rollback Plan**:
  - [Rollback command/steps or declaration of irreversibility]
- **Proposed Action / Resolution Options**:
  ```bash
  [Command / Mutation / Resolution Proposal]
  ```

> Awaiting explicit user approval to proceed.
```

*Completion Criterion*: Report is output to the user and no further tool execution occurs until explicit user approval is granted.
