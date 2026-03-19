---
name: gitnexus-exploring
description: "Explore codebase architecture, trace execution flows, and understand unfamiliar code using GitNexus knowledge graph. Use when asked 'How does X work?', 'What calls this function?', or 'Show me the auth flow'."
---

# Exploring Codebases with GitNexus

Use this skill to navigate and understand a codebase by leveraging the GitNexus knowledge graph.

## Workflow

1. **Discover Repositories**: Read `gitnexus://repos` to identify all indexed repositories.
2. **Check Context**: Read `gitnexus://repo/{name}/context` to get a codebase overview and verify if the index is stale.
   - *Note*: If the index is stale, run `npx gitnexus analyze` in the terminal.
3. **Query Concepts**: Execute `gitnexus_query({query: "<concept>"})` to find execution flows and symbols related to the target area.
4. **Deep Dive on Symbols**: Use `gitnexus_context({name: "<symbol>"})` to see a 360-degree view of a specific symbol (callers, callees, and process participation).
5. **Trace Execution Flows**: Read `gitnexus://repo/{name}/process/{name}` for a step-by-step execution trace of a specific flow.
6. **Inspect Source**: Read implementation details in the source files once the high-level architecture is understood.

## Checklist

- [ ] Read `gitnexus://repo/{name}/context` for overview and staleness check.
- [ ] Run `gitnexus_query` for the concept you want to understand.
- [ ] Review returned processes (execution flows).
- [ ] Run `gitnexus_context` on key symbols for callers/callees.
- [ ] Read process resource for full execution traces.
- [ ] Read source files for implementation details.

## Resources Reference

| Resource | Description |
| :--- | :--- |
| `gitnexus://repo/{name}/context` | Stats and staleness warning. |
| `gitnexus://repo/{name}/clusters` | Functional areas with cohesion scores. |
| `gitnexus://repo/{name}/cluster/{name}` | Area members with file paths. |
| `gitnexus://repo/{name}/process/{name}` | Step-by-step execution trace. |

## Tools Reference

- **gitnexus_query**: Find execution flows related to a concept.
- **gitnexus_context**: Get a 360-degree view of a symbol (incoming/outgoing calls, processes).

## Example: "How does payment processing work?"

1. Read `gitnexus://repo/my-app/context` to verify index status.
2. Run `gitnexus_query({query: "payment processing"})` to identify flows like `CheckoutFlow`.
3. Run `gitnexus_context({name: "processPayment"})` to see its callers and callees.
4. Read `gitnexus://repo/my-app/process/CheckoutFlow` for the full trace.
5. Read `src/payments/processor.ts` for implementation details.
