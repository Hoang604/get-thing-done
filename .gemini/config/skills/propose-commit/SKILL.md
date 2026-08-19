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
  1. **Context & Motivation (Why)**: 1–2 direct sentences describing the previous state, limitation, or problem that prompted the change.
  2. **Key Technical Decisions (How/What)**: 2–3 concise bullet points (`- `) highlighting structural changes, interfaces, error-handling rules, or non-obvious trade-offs.

### 3. Constraints & Tone
- Focus on **Why** and **Key Decisions**, never list file names or chronological steps.
- Ban generic AI fluff (e.g., "improve maintainability", "enhance modularity", "streamline workflow", "clean up code"). Use concrete technical terms.
- Strip all pronouns, filler words, and attribution (no "I", "we", "this commit").
- Drop all fluff, give most concise message.
