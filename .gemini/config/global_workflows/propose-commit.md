---
name: propose-commit
description: Propose a conventional commit message for the current changes.
disable-model-invocation: true
---

Propose commit message for the entire change from the active session. Focus on your compacted context if there is, plus the current context window.
Propose commit message only if user asks. Use Conventional Commits (Types: feat, fix, refactor, perf, docs, test, chore, build, ci, style, revert). Document the underlying problem and technical motivation.

- Subject: `<type>(<scope>): <imperative motivation>`
- Compress all context into the subject. Use body only if subject is insufficient.
- Write clinical facts. Strip pronouns, filler, emojis, filenames, and AI attribution (e.g., "This commit", "I", "we", "now", "As requested").
