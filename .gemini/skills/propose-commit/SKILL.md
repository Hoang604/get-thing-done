---
name: propose-commit
description: Propose a conventional commit message for the current changes.
disable-model-invocation: true
---

Treat the entirety of your available memory (compacted context and active window) as a single, indivisible unit of work. Synthesize every action, bug fix, and feature present in this memory into one comprehensive commit message.

- **Final State Only**: Describe the achieved structural state and unlocked capabilities. Do not write a chronological log of actions taken or work done.

Propose commit message only if user asks. Use Conventional Commits (Types: feat, fix, refactor, perf, docs, test, chore, build, ci, style, revert). Document the underlying problem and technical motivation.

- Subject: `<type>(<scope>): <imperative motivation>`
- Compress all context into the subject. Use body only if subject is insufficient.
- Write clinical facts. Strip pronouns, filler, emojis, filenames, and AI attribution (e.g., "This commit", "I", "we", "now", "As requested").

- **Body Format**: Use bullet points (`- `) for distinct architectural changes or motivations. Separate subject and body with a blank line.
