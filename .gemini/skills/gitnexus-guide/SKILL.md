---
name: gitnexus-guide
description: "Reference for GitNexus tools, resources, graph schema, and workflow mapping. Use when asked 'What GitNexus tools are available?' or 'How do I use GitNexus?'."
---

# GitNexus Guide

Use this skill as a quick reference for all GitNexus MCP tools, resources, and the knowledge graph schema.

## Getting Started

For any task involving code understanding, debugging, impact analysis, or refactoring:

1. **Check Context**: Read `gitnexus://repo/{name}/context` to get a codebase overview and verify index freshness.
2. **Select Skill**: Match your task to one of the specialized GitNexus skills:
   - **Architecture/Exploration**: `gitnexus-exploring`
   - **Safety/Impact Analysis**: `gitnexus-impact-analysis`
   - **Debugging/Bug Tracing**: `gitnexus-debugging`
   - **Refactoring/Restructuring**: `gitnexus-refactoring`
   - **CLI/Indexing**: `gitnexus-cli`
3. **Follow Workflow**: Read the selected skill file and follow its structured workflow and checklist.

## Tools Reference

| Tool | Description |
| :--- | :--- |
| `gitnexus_query` | Find execution flows and symbols related to a concept. |
| `gitnexus_context` | Get a 360-degree view of a symbol (refs, processes). |
| `gitnexus_impact` | Analyze symbol blast radius (upstream/downstream). |
| `gitnexus_detect_changes` | Map current git changes to affected flows and symbols. |
| `gitnexus_rename` | Perform automated, multi-file coordinated renames. |
| `gitnexus_cypher` | Execute raw graph queries (read the schema resource first). |
| `list_repos` | Discover all indexed repositories. |

## Resources Reference

| Resource | Content |
| :--- | :--- |
| `gitnexus://repo/{name}/context` | Stats and staleness check. |
| `gitnexus://repo/{name}/clusters` | Functional areas with cohesion scores. |
| `gitnexus://repo/{name}/cluster/{name}` | Area members and file paths. |
| `gitnexus://repo/{name}/processes` | All detected execution flows. |
| `gitnexus://repo/{name}/process/{name}` | Step-by-step execution trace. |
| `gitnexus://repo/{name}/schema` | Graph schema for Cypher queries. |

## Graph Schema Reference

- **Nodes**: `File`, `Function`, `Class`, `Interface`, `Method`, `Community`, `Process`.
- **Edges** (via `CodeRelation.type`): `CALLS`, `IMPORTS`, `EXTENDS`, `IMPLEMENTS`, `DEFINES`, `MEMBER_OF`, `STEP_IN_PROCESS`.

### Example Cypher Query
```cypher
MATCH (caller)-[:CodeRelation {type: 'CALLS'}]->(f:Function {name: "myFunc"})
RETURN caller.name, caller.filePath
```
