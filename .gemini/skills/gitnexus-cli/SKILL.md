---
name: gitnexus-cli
description: "Manage GitNexus indexing, status, and documentation using CLI commands. Use when asked to 'Index this repo', 'Reanalyze the codebase', or 'Generate a wiki'."
---

# GitNexus CLI Commands

Use this skill to manage the GitNexus knowledge graph and documentation through the command-line interface. All commands are executed via `npx`.

## Core Commands

### analyze — Build or refresh the index

```bash
npx gitnexus analyze
```

Run this from the project root to parse source files, build the knowledge graph, and generate context files (`AGENTS.md`).

| Flag | Effect |
| :--- | :--- |
| `--force` | Force a full re-index even if the index is up to date. |
| `--embeddings` | Enable embedding generation for semantic search (off by default). |

**When to run**: First time in a project, after major code changes, or when the index is reported as stale.

### status — Check index freshness

```bash
npx gitnexus status
```

Shows if the current repository has a GitNexus index, its last update time, and symbol/relationship counts.

### clean — Delete the index

```bash
npx gitnexus clean
```

Deletes the `.gitnexus/` directory and unregisters the repository from the global registry.

| Flag | Effect |
| :--- | :--- |
| `--force` | Skip the confirmation prompt. |
| `--all` | Clean all indexed repositories in the global registry. |

### wiki — Generate documentation

```bash
npx gitnexus wiki
```

Generates repository documentation from the knowledge graph using an LLM. Requires an API key.

| Flag | Effect |
| :--- | :--- |
| `--force` | Force full regeneration of the wiki. |
| `--model <model>` | Specify the LLM model (default: minimax/minimax-m2.5). |
| `--api-key <key>` | Provide the LLM API key. |

### list — Show all indexed repos

```bash
npx gitnexus list
```

Lists all repositories registered in the global GitNexus registry (`~/.gitnexus/registry.json`).

## Troubleshooting

- **"Not inside a git repository"**: Ensure you are running the command from within a git repository.
- **Index is stale after re-analyzing**: Restart the Gemini CLI or reload the MCP server to ensure the latest index is loaded.
- **Embeddings are slow**: Omit the `--embeddings` flag or ensure a fast LLM API key is configured.
