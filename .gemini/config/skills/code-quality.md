# Code Quality Defenses

Before writing code, map the established Phase 1 Alignment Contract to the mechanisms below. Declare every active mechanism and state exactly how it forces your execution. Output a list:
`- **[Mechanism Name]**: [How it forces execution]`

- **APIs & Methods**: When calling an API, read the target class/struct definition to verify exact signature and attributes before writing the call.
- **Dependencies**: When importing a module, read package/dependency config files to verify library exists.
- **Data & I/O Performance**: When writing loops, batch DB/network calls before the loop. When inside an async context, use async equivalents for all I/O. When fetching data, paginate access or yield lazily via generators. When calculating numerical data, use vectorized operations or slices. When concatenating text, use string builders/joiners.
- **Concurrency**: When writing check-then-act sequences, wrap state mutations in atomic operations or synchronization primitives (`mutexes`, `rwlocks`, `asyncio.Lock`, DB `SELECT ... FOR UPDATE`, distributed `Redis` locks). When holding a lock, extract all DB queries, network calls, and I/O outside the lock boundary. Hold locks only for fast, in-memory state mutations.
- **State & Resources**: When transforming data, return the new state as a direct output to keep functions pure. When opening external connections or files, wrap them in native context managers (or `defer`).
- **Error Handling & Types**: When handling exceptions, catch specific typed exceptions and throw specific error classes. When state corrupts, crash the process explicitly to fail fast. When accessing nullable variables, validate the null state before access. Enforce strict type hints on all signatures.
- **Architecture**: When writing complex logic, extract independent operations into isolated helper functions. When solving standard problems, import standard library algorithms. When hardcoding magic numbers or configuration strings, extract them to constants or environment variables.
- **Testing**: When writing tests, assert against external observable outputs. When faking dependencies, mock only external system boundaries (disk/network). Use real objects for all internal logic.
