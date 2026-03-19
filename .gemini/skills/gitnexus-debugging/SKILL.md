---
name: gitnexus-debugging
description: "Debug bugs, trace errors, and investigate unexpected behavior using GitNexus. Use when asked 'Why is X failing?', 'Where does this error come from?', or 'Trace this bug'."
---

# Debugging with GitNexus

Use this skill to identify the root cause of bugs and errors by tracing execution flows and call chains through the GitNexus knowledge graph.

## Workflow

1. **Search Symptoms**: Execute `gitnexus_query({query: "<error or symptom>"})` to find related execution flows and symbols.
2. **Identify Suspects**: Analyze the returned processes and symbols to identify functions or modules likely involved in the failure.
3. **Analyze Context**: Use `gitnexus_context({name: "<suspect>"})` to see callers, callees, and process participation for the suspect symbol.
4. **Trace Execution**: Read `gitnexus://repo/{name}/process/{name}` for a full, step-by-step execution trace of the relevant flow.
5. **Custom Traces**: Use `gitnexus_cypher({query: "MATCH path..."})` for custom call chain traces if standard flows are insufficient.
6. **Confirm Root Cause**: Read the source files for the suspect functions to confirm the logic error.

## Debugging Patterns

| Symptom | GitNexus Approach |
| :--- | :--- |
| **Error message** | `gitnexus_query` for error text → `context` on throw sites. |
| **Wrong return value** | `context` on the function → trace callees for data flow. |
| **Intermittent failure** | `context` → look for external calls or async dependencies. |
| **Performance issue** | `context` → find symbols with many callers (hot paths). |
| **Recent regression** | `detect_changes` to see what recent changes affected. |

## Checklist

- [ ] Understand the symptom (error message, unexpected behavior).
- [ ] Run `gitnexus_query` for error text or related code.
- [ ] Identify suspect functions from the results.
- [ ] Run `gitnexus_context` to see callers and callees.
- [ ] Trace the execution flow via the process resource.
- [ ] Use `gitnexus_cypher` for custom call chain traces if needed.
- [ ] Inspect source files to confirm the root cause.

## Example: "Payment endpoint returns 500 intermittently"

1. Run `gitnexus_query({query: "payment error handling"})` to identify `CheckoutFlow` and `validatePayment`.
2. Run `gitnexus_context({name: "validatePayment"})` to see its outgoing calls.
3. Observe that it calls `fetchRates` (an external API).
4. Read `gitnexus://repo/my-app/process/CheckoutFlow` to see the full trace.
5. Identify that `fetchRates` lacks a timeout, causing intermittent 500s when the external API is slow.
