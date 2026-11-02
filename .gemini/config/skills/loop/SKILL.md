---
name: loop
description: Execute a root-to-leaf refinement pass directly on the workspace by mapping the task's dependency DAG into a persistent artifact and working through every node from root to leaf
disable-model-invocation: true
---

# CORE DIRECTIVE

Map the dependency graph of the code participating in the task into `<appDataDir>/brain/<conversation-id>/loop_dag.md`, and work through `loop_dag.md` in topological order from **root nodes** to **leaf nodes** directly on the workspace without pausing for confirmation, reading the live code on disk at each node and refining the implementation against the user's request until every gap and residue is resolved.

> [!IMPORTANT]
> **The Job Principle (Scope & Users):**
> Trace outward from every module the task touches along everything that invokes or registers it for as long as those callers remain within the code the task permits creating or modifying (`mutable scope`). The outermost boundary where callers sit outside that mutable scope is the **entry boundary**, the boundary where results return across it is the **exit boundary**, and the external actors that invoke the entry boundary or consume what crosses the exit boundary are the **users**; code inside the mutable scope is the implementation, never a user.
> Each user's **job** is what that external actor is trying to get done across the mutable scope. Everything inside the mutable scope required for users to finish their jobs without **friction**—any moment where a user must know or do something its job does not require—is in scope, including what the request left unwritten; anything serving a different job is out of scope.

> [!IMPORTANT]
> **Minimal System Entropy & The Day-One Test:**
> Diff measures transition cost; entropy measures structural disorder. A change achieves minimal entropy only when the resulting codebase has exactly one canonical way to represent and execute the concept, leaving zero structural residue from the transition.
> Everything the change touches or makes obsolete must take the form it would have had if the system had been designed for its current requirements from day one. Any form whose justification needs the code's past instead of the system's present requirements is **residue**.

---

## Maximal Yield & Deep Module Principles

Every technical decision answers to one principle:

> **Each change leaves everything outside the module with less to know and less to change than before.**

Outside the module is anything that interacts with it without seeing inside it, the users included.

- **Less to know (`Deep vs Shallow Modules`).** A **module** is any unit with an interface and an implementation. A module's **interface** is everything a caller must know to use it correctly; **when** correct use requires knowing anything its signature does not state, the interface leaks. Design **deep modules** (`lots of behavior hidden behind a small, simple interface`) and reject **shallow modules** (`large interface, thin pass-through implementation`).
- **Side-Effect Isolation.** Interfaces must make all state transitions explicit in their return contract rather than mutating caller or global state behind the caller's back. Inject external I/O adapters strictly as parameters.
- **Less to change (`Decoupled & Open-Closed`).** When behaviour later varies or evolves, the change lands inside the module and code outside stays as it is. This judges the shape the change leaves behind, never the size of the change itself: edits outside the module that remove a pre-change form are what the Day-One Test demands. When the requirements or codebase carry two or more variants of behaviour, isolate variation so adding a variant lands as new code beside existing code rather than mutating callers; when only a single concrete variant exists, keep it direct without speculative indirection.
- **The Deletion Test.** For every structure or module the change introduces, imagine deleting it. If complexity reappears across its callers, the structure earns its place. If complexity collapses without loss, the structure was an accidental shallow pass-through and must not exist.
- **Seams.** A **seam** is where a swappable boundary lives. **One adapter means a hypothetical seam; two adapters means a real one.** Introduce seams strictly when justified by at least two adapters. Keep all internal seams strictly private within the module.

---

## Execution Workflow

### Step 1: Dependency DAG Construction (`loop_dag.md`)

Identify every external **user** and its **job** across the **entry boundary** and **exit boundary** (`The Job Principle`), trace the dependency structure of the code within the mutable scope from **root** (upstream foundations that other code depends on) to **leaf** (downstream consumers that depend on upstream code), and write both the user jobs and the dependency graph to `<appDataDir>/brain/<conversation-id>/loop_dag.md` (`UserFacing: true, RequestFeedback: false`). Place a directed edge $A \to B$ whenever $B$ depends on $A$, so the traversal walks from foundational roots (`Upstream Dependencies: None`) to downstream leaves rather than modifying downstream dependents before upstream foundations.

Each node $B$ in `loop_dag.md` contains strictly two fields:
1. **Upstream Dependencies:** The parent nodes $\{A \mid A \to B\}$ that $B$ depends on (`None` for root nodes).
2. **Anchor Files:** The starting files on disk for $B$ (acting as entry points for $B$ without restricting $B$ solely to those files).

- **Completion Criterion:** Every user outside the mutable scope is identified with its job, and `<appDataDir>/brain/<conversation-id>/loop_dag.md` is written to disk containing the dependency path from **root nodes** to **leaf nodes** with each node's two fields before Step 2 begins.

---

### Step 2: Root-to-Leaf Execution & Refinement

Walk through `<appDataDir>/brain/<conversation-id>/loop_dag.md` in topological order from **root nodes** to **leaf nodes**:

1. **Read Live Code Along the Path:** As you traverse each node in `loop_dag.md`, starting from its **Anchor Files**, use `rg` and call `read_file` across all files participating in that node and every place in the workspace whose behavior or continued existence depends on it (never skipping any node or file in `loop_dag.md` because an upstream edit already touched it).
2. **Refine Continuously From Root to Leaf:** Throughout the root-to-leaf traversal, **when** the code on disk falls short of the user's request or the principles in this skill, edit every affected file across the workspace to resolve it on disk and continue advancing along `loop_dag.md` until the entire path from **root nodes** to **leaf nodes** has been read and refined.
3. **Verify:** Once every node from root to leaf in `loop_dag.md` has been traversed and refined on disk, run the workspace verification/test commands and report completion with the verification check results.

- **Completion Criterion:** The full path in `loop_dag.md` from **root nodes** to **leaf nodes** had its participating files and dependent workspace places read with `read_file`, every place falling short of the user's request or the principles in this skill was resolved on disk, and verification checks succeeded.
