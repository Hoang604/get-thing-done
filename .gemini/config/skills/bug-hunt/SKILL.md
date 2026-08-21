---
name: bug-hunt
description: Autonomous iterative red/green bug hunt and repair loop driven by blind fresh-context audit subagents and resolution proofs.
disable-model-invocation: true
---

# Bug Hunt Skill

Execute an iterative red/green audit and repair loop across the codebase. In each turn, spawn an isolated, fresh-context subagent that scans the entire codebase blindly against `./.gtd/PRODUCT.md` (with zero access to previous reports to prevent anchoring bias). The primary agent remediates all reported defects, validates fixes, and records resolution proof until achieving a clean pass or reaching 5 turns.

---

## Steps

### 1. Ground Truth Gate & Initialization
1. Verify existence of `./.gtd/PRODUCT.md`.
2. When `./.gtd/PRODUCT.md` is absent, stop and instruct user to run `/product-truth`.
3. Capture session timestamp: `TIMESTAMP=$(date +"%Y%m%d-%H%M%S")`.
4. Initialize turn counter: `TURN=1`.

**Completion Criterion**: `./.gtd/PRODUCT.md` confirmed present, `TIMESTAMP` recorded, `TURN` set to 1.

### 2. Blind Fresh-Context Audit (Subagent Turn N)
Construct a prompt with interpolated `${TIMESTAMP}` and `${TURN}` values. Spawn a `self` subagent via `invoke_subagent`.

#### Dynamic Prompt Template (Interpolate `${TIMESTAMP}` and `${TURN}` before sending):
```
When starting audit, read `./.gtd/PRODUCT.md` to load system ground truth invariants.

Scan the entire codebase to find all bugs, logic errors, and violations of `./.gtd/PRODUCT.md`.

Operational Boundaries:
- Perform read-only exploration and analysis.
- Write findings exclusively to `./.gtd/bug-hunt/${TIMESTAMP}/turn-${TURN}/report.md` conforming to the Audit Report Schema.
- Once written, return a final message stating the verdict: "VERDICT: <CLEAN | BUGS_FOUND> (<count> defects) - Path: ./.gtd/bug-hunt/${TIMESTAMP}/turn-${TURN}/report.md".
```

**Completion Criterion**: Subagent exits and `./.gtd/bug-hunt/${TIMESTAMP}/turn-${TURN}/report.md` exists with valid schema.

### 3. Remediation & Verification Proof (Primary Agent)
Read `./.gtd/bug-hunt/${TIMESTAMP}/turn-${TURN}/report.md`.

- **On Verdict `CLEAN`**:
  - Present final clean audit outcome to user.
  - Terminate workflow.

- **On Verdict `BUGS_FOUND`**:
  - Apply source code mutations to resolve every defect listed in `report.md`.
  - Execute test suite, typecheck, or lint verification commands to prove resolution.
  - Write `./.gtd/bug-hunt/${TIMESTAMP}/turn-${TURN}/resolved.md` matching the Resolution Schema.

**Completion Criterion**: All reported defects resolved in source code, verification commands pass with clean status, and `resolved.md` is recorded.

### 4. Turn Advancement & Boundary
- When `TURN == 5`: Present 5-turn completion summary and terminate.
- When `TURN < 5`: Set `TURN = TURN + 1` and proceed to **Step 2** with a fresh-context subagent.

---

## Schemas

### Audit Report Schema (`report.md`)
```markdown
# Audit Report: Turn <N>

## Verdict: <BUGS_FOUND | CLEAN>
Total Defect Count: <count>

## Findings
### [DEFECT-001] <Concise Title>
- **Severity**: <Critical | Major | Minor>
- **Target**: [<filepath>:<line>](file:///<filepath>#L<line>)
- **Ground Truth Breach**: <Specific rule from PRODUCT.md or failure condition>
- **Mechanism**: <Technical description of failure mechanism>
- **Proof of Failure**: <Failing input, test case, or execution trace>
```

### Resolution Schema (`resolved.md`)
```markdown
# Resolution Report: Turn <N>

## Remediation Matrix
### [DEFECT-001] <Concise Title>
- **Mutations Applied**: [<filepath>](file:///<filepath>#L<start>-L<end>) - <Summary of patch>
- **Verification Proof**:
  - Command: `<executed verification / test command>`
  - Result: `<passing output summary>`
  - Invariant Status: Restored
```
