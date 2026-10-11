---
name: trace-flow
description: Trace an end-to-end execution flow through the codebase and generate an architectural causal report
disable-model-invocation: true
---

A code flow is an unbroken causal chain: a trigger injects raw state across an ingress membrane, which undergoes invariant-guarded transformations along an execution spine, terminating in a response and persistent side effects.

## Execution Steps

### 1. Locate Ingress & Membrane
Identify the boundary entrypoint receiving external stimulus.
- Pinpoint the physical symbol admitting the incoming stimulus.
- Extract the raw contract shape and boundary admission criteria.
- **Completion Criterion**: The entrypoint symbol and admission guard assertions are identified with file paths and line numbers.

### 2. Trace the Execution Spine & Lineage
Construct the unbroken execution sequence from ingress to terminal egress.
- Record each successive invocation or dispatch hop, capturing state transformations and invariant guards at each transition.
- Assert causal continuity: every transition must map directly from predecessor to successor without omitting intermediate layers.
- **Completion Criterion**: Every execution hop, state transition, and accompanying guard condition from entrypoint to termination is verified in code and recorded as an unbroken sequence.

### 3. Isolate Egress & Side Effects
Determine the terminal outcome and all external mutations.
- Identify the terminal response emitted to the caller.
- Record all state mutations persisting beyond volatile process memory.
- **Completion Criterion**: Terminal response contract and all out-of-process mutations are cataloged with explicit call sites.

### 4. Emit Flow Report
Write the findings to an artifact.
- Must include a mermaid diagram visualizing the execution flow.
- Present all discovered elements within the requested scope using whatever structure and style best communicates the causal chain.
- **Completion Criterion**: An artifact is emitted containing the trace findings, a mermaid diagram, and verified source links for every referenced code symbol.

## Boundary Clips

- Every step in the spine must resolve to an existing, verifiable code symbol.
- Classify components by structural role (Ingress, Spine, Membrane, Egress), not vendor technology labels.
