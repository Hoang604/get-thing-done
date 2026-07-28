# Anti-Hallucination & Verification

- **Logic Verification**: When evaluating behavior, read the implementation body to define exact logic. 
- **Diagnosis**: When diagnosing runtime errors or answering bug questions, isolate the exact line, variable, and mechanical state mismatch. Report facts only. Guardrail: Diagnosis is always `[CONSULT]`.
- **Impact Analysis**: When deleting or modifying a function signature, run `grep_search` to find and update all exact callers across the workspace.
- **End-to-End Exploring**: When tracing how a feature works, mechanically trace the complete execution chain: read entry point (router/controller), business logic, output, persistence, and implementation code paths.
