---
name: loop
description: Execute an N-iteration refinement loop directly on the workspace by mapping the task's dependency DAG into a persistent artifact and working through every node from root to leaf across all N iterations
disable-model-invocation: true
---

# CORE DIRECTIVE

Extract the iteration cap $N$ from the user's request (**When** the user does not specify $N$, set $N = 3$), map the dependency graph of the code participating in the task into `<appDataDir>/brain/<conversation-id>/loop_dag.md`, and execute all iterations sequentially from $i = 1$ to $N$ directly on the workspace without pausing for confirmation. In every iteration $i$, work through `loop_dag.md` in topological order from **root nodes** to **leaf nodes**, reading the live code on disk from scratch at each node and refining the implementation against the user's request until every gap and residue is resolved.

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

Before iteration $1$, trace across the mutable scope between the task's **entry boundary** and **exit boundary** (`The Job Principle`) to break the code participating in fulfilling the user's request into dependency nodes, and write the dependency DAG to `<appDataDir>/brain/<conversation-id>/loop_dag.md` (`UserFacing: true, RequestFeedback: false`) before editing any workspace file. A directed edge $A \to B$ exists from upstream node $A$ to downstream node $B$ whenever $B$ relies on capability or behavior provided by $A$, so $A$ must be settled on disk before $B$ is built or refined; nodes with no upstream dependencies in the graph are the **root nodes**, and nodes with no downstream dependents in the graph are the **leaf nodes**.

Each node $B$ in `loop_dag.md` contains strictly two fields:
1. **Upstream Dependencies:** The parent nodes $\{A \mid A \to B\}$ that $B$ depends on (`None` for root nodes).
2. **Anchor Files:** The files on disk where $B$ lives, serving as the starting point when working on $B$.

Across all iterations $i = 1 \dots N$, **when** reading or editing code on disk reveals a participating module or a dependency edge $A \to B$ not yet reflected in `loop_dag.md`, update `loop_dag.md` so the dependency graph matches the codebase.

- **Completion Criterion:** Every user outside the mutable scope is identified with its job, and `<appDataDir>/brain/<conversation-id>/loop_dag.md` is written to disk containing all participating nodes from **root nodes** to **leaf nodes** with each node's two fields before iteration $1$ begins.

---

### Step 2: $N$-Iteration Root-to-Leaf Execution & Refinement ($i = 1 \dots N$)

Execute all iterations $i = 1 \dots N$ sequentially. In every iteration $i$ ($1 \dots N$), read `<appDataDir>/brain/<conversation-id>/loop_dag.md` and work through the DAG from **root nodes** to **leaf nodes**, building and refining each node $B$ only after every upstream dependency $A$ ($A \to B$) has been completed in iteration $i$:

1. **Per-Node Blast-Radius Expansion (Before Editing $B$):** At each node $B$, starting from its **Anchor Files**, before editing any file for $B$ or advancing to a downstream node, use `rg` and call `read_file` within iteration $i$ itself on every file implementing $B$ and every place in the workspace whose behavior or validity depends on $B$ or that still retains anything made obsolete by $B$ (never reusing `read_file` outputs from an earlier iteration $< i$ or stopping `read_file` discovery upon spotting the first defect):
   - **When** adapting an affected place $C$ inside the mutable scope is absorbed entirely within $C$ without changing what $C$ exposes to its own callers or consumers: update $C$ directly while working on $B$.
   - **When** adapting $C$ changes what $C$ exposes to its own callers or consumers, creating a further blast radius behind $C$: add $C$ as a downstream node ($B \to C$) in `loop_dag.md` so iteration $i$ builds and refines $C$ in topological order.
2. **Build & Refine:** After completing all `rg` discovery and `read_file` calls for $B$ in iteration $i$, implement and refine $B$ and its expanded scope on disk against the user's request and its settled upstream dependencies $\{A \mid A \to B\}$, resolving every gap, flaw, or residue on disk before advancing to any downstream node.
   - **When** fulfilling the user's request at $B$ requires a decision absent from both the request and the codebase, or cannot hold against a physical constraint in the codebase, stop execution immediately and report `BLOCKED: <reason with file:line>`.
3. **Verify & Advance Iteration:** Once every node from root to leaf in `loop_dag.md` (including any downstream node added during iteration $i$) has been completed on disk for iteration $i$, run the workspace verification/test commands.
   - **When** $i < N$: announce that iteration $i/N$ is complete and explicitly state that iteration $(i + 1)/N$ begins now by re-reading `loop_dag.md` and working through every node from **root nodes** to **leaf nodes** from scratch—running fresh `rg` discovery and `read_file` calls on the live disk files of every node and its dependents (never reusing reads from iteration $\le i$ or skipping a node because an earlier iteration already edited it) to expand its blast radius and refine the code on disk until every remaining gap and residue is resolved—then immediately call `read_file` on `loop_dag.md` to start iteration $i + 1$.
   - **When** $i = N$: stop the loop and report final completion at iteration $N/N$ with the verification check results.

- **Completion Criterion:** In every iteration $i$ ($1 \dots N$), every node $B$ in `loop_dag.md` from **root nodes** to **leaf nodes** had its full implementation and dependent workspace places freshly read with `read_file` within iteration $i$, every gap against the user's request and every residue was resolved on disk, verification checks succeeded after each iteration $i$, and all $N$ iterations executed through iteration $N/N$.

---

## Compaction Summary & Resume Override

**When** `loop` is active, it overrides Section 3 (`Settled state and open work`) and the resume step of `<context_and_transcript_rules>`:

- **In `<summary>` Section 2 (`Read-next working set`):** Always include this skill's `SKILL.md` path and the full `<appDataDir>/brain/<conversation-id>/loop_dag.md` alongside the unread `file:start-end` slices needed for the active node $B$ of the current iteration $i$.
- **In `<summary>` Section 3 (`Settled state and open work`):** Apply the settled-versus-open rules of `<context_and_transcript_rules>` scoped strictly to the active iteration $i$ rather than the cumulative conversation:
  1. **Loop Cursor:** `Iteration i / N — Active Node: <B>` (current iteration index $i$, total iteration cap $N$, and current node in `loop_dag.md`).
  2. **Current Iteration ($i$) Settled State:** Only state that became settled during iteration $i$ itself (which nodes in `loop_dag.md` have completed iteration $i$, plus `file:line` observations and disk edits made in iteration $i$). Every observation and node completion from any earlier iteration ($< i$) expires when iteration $i$ begins and is omitted.
  3. **Current Iteration ($i$) Open Work:** The active node $B$ and all remaining incomplete downstream nodes in `loop_dag.md` for iteration $i$, followed by iterations $i + 1 \dots N$.
- **Upon Resume after Compaction:** On the first turn after compaction, state `Iteration i / N`, which nodes of `loop_dag.md` are completed within iteration $i$, and which nodes remain in iteration $i$; read `SKILL.md`, the entire `loop_dag.md`, and the `Read-next working set` in one batch, finish iteration $i$ from the active node $B$ to the leaf nodes, and continue the loop through iteration $N$.
