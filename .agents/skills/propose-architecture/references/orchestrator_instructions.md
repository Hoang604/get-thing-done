# Core Directive

Orchestrate macro architectural proposals across subsystems by constructing a Directed Acyclic Graph of boundaries, delegating design and contracts to isolated boundary crafters, and synthesizing a unified architectural specification.

---

## 1. Context Ingress & Reality Mapping

Read the assigned task file, then read all referenced files inside it concurrently as your starting point.
Survey codebase reality to map the full blast radius of required modifications, while identifying the immutable invariants that govern the domain.

- **Completion Criterion**: Ground the blast radius and governing invariants in physical codebase evidence before constructing the boundary graph.

## 2. Boundary Decomposition & DAG Construction

Partition the surveyed blast radius into isolated boundary nodes, wire their contract dependencies into a Directed Acyclic Graph, and write the topological specification to `.gtd/<task-name>/dag-v1.md`.

### Generative Principle
A boundary encapsulates a design decision that is likely to change, hiding its complexity behind a simple interface.

Decompose the system mechanically by applying three invariant operations:
- **Merge**: Components that share internal mutable state or exhibit bidirectional dependencies share the same design decision and must collapse into a single boundary.
- **Split**: Split any component that encapsulates more than one independent design decision.
- **Prune**: Reject any boundary whose interface is as complex as its implementation.

### Physical Graph Contract
Decompose the architecture into a Directed Acyclic Graph. For every boundary node, specify:
- `boundary_name`: Unique boundary identifier slug.
- `capability`: The observable outcome this boundary enables, defined strictly by what it makes possible rather than how it operates.
- `starting_points`: Known entry files or modules anchoring this boundary.
- `dependencies`: Direct upstream boundary identifiers whose exported contracts this boundary depends on.

- **Completion Criterion**: Write the complete graph specification in topological order to `.gtd/<task-name>/dag-v1.md`. Verify that the graph is strictly acyclic and that every boundary is grounded in known starting points.

## 3. DAG Execution & Boundary Dispatch

Execute boundaries strictly by topological dependencies defined in `.gtd/<task-name>/dag-v1.md`. Spawn a boundary node if and only if every upstream dependency has delivered its exported contract.

For each eligible boundary node:
1. Package context:
   - Original specification files.
   - Assigned boundary starting points.
   - Exported contracts of direct upstream dependencies at `.gtd/<task-name>/<prev-boundary_name>/contract.md`, this can be one or multiple files.
2. Write the task dispatch file to `.gtd/<task-name>/<boundary_name>/task.md` matching this physical contract without inventing any thing else:
   ```markdown
   # Task Dispatch: <boundary_name>

   ## 1. Capability
   <The observable outcome this boundary enables for the system, defined strictly by what it makes possible rather than how it operates>

   ## 2. Upstream Contracts
   - [.gtd/<task-name>/<dep>/contract.md](file://...)

   ## 3. Starting Points & Context
   - Spec: [<path-to-spec.md>](file://...)
   - Entry points:
     - [<path/to/entry_file>.ts](file://...) <!--starting_points and any other files your just found to belong to the scope-->

   ## 4. Deliverables
   - Final Proposal: `.gtd/<task-name>/<boundary_name>/proposal.md`
   - Exported Contract: `.gtd/<task-name>/<boundary_name>/contract.md`
   ```

3. Resolve the absolute path to `boundary_crafter_instructions.md` located in the same directory as this instructions file (`dirname`). Never read this reference file into the Orchestrator context. Spawn a brand new `self` subagent with role `Boundary Crafter` using this standardized invocation prompt:
   `Execute boundary architecture according to instructions at <boundary_crafter_instructions_path> using task context from .gtd/<task-name>/<boundary_name>/task.md`
4. Await completion confirmation. Upon delivery, inspect the new proposal and contract to verify if the remaining unexecuted boundaries in the active DAG specification require adjustment. If adjustments are required, write a new `.gtd/<task-name>/dag-v<N>.md` file, copying all unaffected boundaries and fields verbatim from version N-1 with zero drift before dispatching subsequent nodes.

## 4. Circuit-Breaker Escalation

When a Boundary Crafter escalates an unresolvable invariant contradiction, package the contradiction summary and evidence with the artifact link, sending an escalation message to the Main Agent for human resolution. stop your work after this, wait for next instruction.

## 5. System Synthesis

Upon completion of all boundary nodes, author `.gtd/<task-name>/architectural_proposal.md` as an executive system blueprint mapping end-to-end dataflow and indexing individual boundary deliverables without duplicating existing proposals or contracts. Highlight the pivotal architectural decisions and core trade-offs across all boundaries, ensuring the entire overview is readable in under five minutes. Record completion in `.gtd/<task-name>/communicate/orchestrator_complete.md` and report the final proposal link to the Main Agent.
