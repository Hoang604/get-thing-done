---
name: loop
description: Execute a root-to-leaf refinement pass directly on the workspace by mapping the task's dependency DAG into a persistent artifact and working through every node from root to leaf
disable-model-invocation: true
---

## Design Principles

- **The Job Principle (`Scope & Users`).** Trace outward from every module the task touches along everything that invokes or registers it for as long as those callers remain within the code the task permits creating or modifying (**mutable scope**): the outermost boundary where callers sit outside that mutable scope is the **entry boundary**, the boundary where results return across it is the **exit boundary**, and the external actors that invoke the entry boundary or consume what crosses the exit boundary are the **users** (code inside the mutable scope is the implementation, never a user). **When** a behavior in the **mutable scope** bears on a **user** interaction across those boundaries, include everything required for each user to finish its **job**—what that external actor is trying to get done across the mutable scope—without **friction** (any moment where a user must know or do something its job does not require), including what the request left unwritten, and exclude anything serving a different job.
- **Minimal System Entropy (`The Day-One Test`).** **When** changing how a concept is represented or executed, bring everything the change touches or makes obsolete into the single canonical form it would have had if the system had been designed for its current requirements from day one, removing all **residue**—any form whose justification needs the code's past instead of the system's present requirements.
- **Explicit Interface Contracts.** A **module** is any unit with an **interface**—everything a caller must know to use it correctly—and an implementation. **When** designing or modifying a module's interface, handle inside the implementation whatever does not require the caller's choice, and state in the signature and return contract everything the caller must supply or observe as an outcome, never mutating caller or global state behind the caller's back.
- **Variation & Seams.** A **seam** is a swappable boundary. **When** the current requirements or codebase contain two or more concrete ways a behavior is fulfilled, isolate that variation behind a seam (kept private inside the module whenever callers do not choose between the cases) so adding a case lands beside existing code without editing callers; **when** a seam sits in front of only one concrete case, collapse it into direct code.
- **The Deletion Test.** **When** a module sits in the resulting design of the touched scope, test deleting that single module while holding all other modules fixed: retain it when deleting it pushes complexity into its callers, and collapse it when complexity disappears without loss.

---

## Execution Workflow

### Step 1: Dependency DAG Construction (`loop_dag.md`)

**When** initial tracing from the task's starting points reveals the external **users** across the **entry boundary** and **exit boundary** (`The Job Principle`) and the dependency flow among the participating areas in the **mutable scope** (without reading every file in full first):

1. State each boundary crossing outside the **mutable scope** individually (citing `file:line`), ruling on the external **user** and **job** it establishes while excluding callers inside the **mutable scope**.
2. Write `<appDataDir>/brain/<conversation-id>/loop_dag.md` (`UserFacing: true, RequestFeedback: false`) from those user rulings and the root-to-leaf dependency graph, placing a directed edge $A \to B$ whenever $B$ depends on $A$ so **root nodes** (`Upstream Dependencies: None`) precede the **leaf nodes** that depend on them, then proceed directly to Step 2 without pausing for confirmation.

Each node in `loop_dag.md` contains strictly two fields—**Upstream Dependencies** (`None` for root nodes, or the parent nodes it depends on) and **Anchor Files** (starting files on disk for that area, without restricting the node solely to those files):

```markdown
## Users & Jobs
- **Cashier (`src/pos_cli.py`):** Ring up an order and print an itemized receipt in one command.

## Dependency DAG (Root -> Leaf)
### 1. `pricing_rules`
- **Upstream Dependencies:** None
- **Anchor Files:** `src/pricing.py`

### 2. `order_summary`
- **Upstream Dependencies:** `pricing_rules`
- **Anchor Files:** `src/order.py`

### 3. `receipt_cli`
- **Upstream Dependencies:** `order_summary`
- **Anchor Files:** `src/pos_cli.py`
```

- **Completion Criterion:** Every boundary crossing outside the **mutable scope** has an individual ruling identifying its **user** and **job**, `<appDataDir>/brain/<conversation-id>/loop_dag.md` is written to disk in the shape above from **root nodes** to **leaf nodes**, and execution advances directly to Step 2.

---

### Step 2: Root-to-Leaf Execution & Refinement

Use `<appDataDir>/brain/<conversation-id>/loop_dag.md` to settle upstream **root nodes** before the downstream **leaf nodes** that depend on them (never modifying downstream leaves before settling the upstream roots they depend on):

1. **Read Live Code & Dependents:** Starting from each node's **Anchor Files** in root-to-leaf order, use `rg` and `read_file` across all files participating in that node and every place in the workspace whose behavior or continued existence depends on it (never skipping any node or file in `loop_dag.md` because an earlier edit already touched it).
2. **Rule Before Editing:** Before emitting any file edit for the scope under refinement, identify every concrete item in that scope and in the state the edit will leave on disk that triggers a **When** condition in **Design Principles**, state that rule's ruling on each item individually while holding all other items fixed (citing `file:line`), and construct the edits on disk strictly from those individual rulings (never grouping items into a shared ruling or justifying edits after writing them).
3. **Verify:** Once every node from root to leaf in `loop_dag.md` and its workspace dependents have been read and refined on disk, run the workspace verification/test commands and report completion with the verification check results.

- **Completion Criterion:** Every node from **root nodes** to **leaf nodes** in `loop_dag.md` and every workspace place depending on it was read with `read_file` with upstream roots settled before downstream leaves, every concrete item triggering **Design Principles** across that scope received an individual pre-edit ruling and matches that ruling on disk, and verification checks succeeded.
