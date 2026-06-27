---
name: explain-architecture
description: Explain the skeleton of the architecture to build the global frame for understanding the codebase
---
Build global frame for understanding unfamiliar codebase.

Do in order:

1. **Organizing principle first:** Plainly state what problem architecture solves/enforces. Event-driven, separation of concerns, etc.
2. **The skeleton:** 3-5 core concepts needed in head before code makes sense. No filenames.
3. **Runtime flow:** Walk through path from entry to output. Use actual codebase names.
4. **Specific piece context:** Slot requested piece into frame. Show role, dependencies, dependents.

Rules:
- No file structures first.
- If asked "what is this", show location in architecture and why.
- If unconventional, name convention broken and tradeoff.
- Short sentences. Real component names. No filler.
- Read code to get context. No guessing.
