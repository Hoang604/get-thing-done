---
name: propose-commit
description: Propose a conventional commit message for the current changes.
disable-model-invocation: true
---

Treat the entirety of your available memory (compacted context and active window) as a single, indivisible unit of work. Synthesize the final state into a high-signal Conventional Commit message.

- **Final State Only**: Describe the achieved structural state and unlocked capabilities. Do not write a chronological log of actions taken or work done.
- Propose commit message only if user asks.

### 1. Subject Line
- Format: `<type>(<scope>): <imperative summary>`
- Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `build`, `ci`, `style`, `revert`.

### 2. Body Strategy
- **Simple Changes**: Output ONLY the subject line.
- **Complex / Architectural Changes**: Include a body with two parts separated by a blank line:
  1. **Context**: 1 direct sentence sythesize why the change is required
  2. **Key achievement**: concise bullet points (`- `) highlighting what final result achieved in the commit, drop all internal process, only cite the result.

### 3. Constraints & Tone
- Ban generic AI fluff (e.g., "improve maintainability", "enhance modularity", "streamline workflow", "clean up code"). Use concrete technical terms.
- Strip all pronouns, filler words, and attribution (no "I", "we", "this commit").
- Drop all fluff, give most concise message.
