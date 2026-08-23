---
name: fix-bug
description: Evidence-driven bug diagnosis and remediation loop using probe instrumentation, log-only diagnosis, and mandatory probe cleanup.
disable-model-invocation: true
---

# Targeted Bug Fixing Protocol

Execute a deterministic, evidence-driven debugging loop. Prohibits speculative guessing from static code reading by enforcing probe logging, evidence capture, log-only diagnosis, minimal structural repair, and complete instrumentation cleanup.

---

## Steps

### 1. Probe Instrumentation
Identify suspect execution paths, seams, and branch conditions. Insert structured debug log statements (probes) capturing:
- Function entry / exit points and argument payloads.
- Branch decisions and predicate evaluation results.
- Intermediate state transitions and error values.

**Completion Criterion**: Debug probes placed along suspect execution paths without modifying application logic.

### 2. Evidence Collection
Execute the reproduction command or test suite to trigger the failure under active probe logging. When local reproduction is not possible, request the reproduction log trace from the user.

**Completion Criterion**: Log trace captured containing concrete execution path and variable values.

### 3. Log-Driven Root Cause Diagnosis
Analyze the captured trace to isolate the exact broken invariant:
- Identify the first point where actual execution diverges from expected invariants.
- Form root-cause conclusion strictly from logged data; eliminate all speculative hypotheses.

**Completion Criterion**: Root cause identified with proof referencing specific log trace lines and variable states.

### 4. Minimal Structural Remediation
Apply minimal targeted code mutation that restores the broken invariant at the root cause seam. Re-run verification commands to confirm the failure is resolved.

**Completion Criterion**: Verification suite passes with clean exit status.

### 5. Mandatory Probe Cleanup
Remove every debug probe and temporary log statement inserted in Step 1. Re-run typechecks, linter, and tests to ensure clean source code.

**Completion Criterion**: Zero debug probe remnants in codebase and all verification gates pass cleanly.
