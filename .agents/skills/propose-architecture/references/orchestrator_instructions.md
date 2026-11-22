# Core Directive

Orchestrate macro architectural design across large multi-boundary systems by anchoring constraints, establishing a shared System Spine, constructing a Directed Acyclic Graph of boundaries, delegating boundary design with bounded contract negotiation, and synthesizing an executive blueprint ready for downstream `boundary-plan` execution.

---

## 1. Context Ingress & Reality Anchoring

1. Read the assigned dispatch file and every file referenced inside it concurrently.
2. **When** the system under design involves realtime multi-user state synchronization, optimistic local mutations, collaborative documents, or stateful room coordination, read `../../boundary-plan/references/realtime-sync.md` to anchor synchronization primitives and invariants in the System Spine.
3. **When** the system under design involves e-commerce checkout, order payment collection, payment webhooks, or customer refunds and cancellations, read `../../boundary-plan/references/ecommerce-payment.md` to anchor PCI scope, durable idempotency, webhook fulfillment, and refund invariants in the System Spine.
4. **When** grounding a boundary during Reality Mapping, evaluate each element of the boundary individually while holding the rest fixed and anchor every claim and invariant in whatever already constrains it before this task runs: every constraint residing in the existing codebase is anchored by a verified `file:line` citation, and every constraint residing outside the codebase is anchored by the authoritative external source that establishes it. Derive `starting_points` strictly as the set of existing codebase anchors identified for that boundary, and reject only claims whose required anchor is missing or contradicted.

- **Completion Criterion**: Every relevant codebase constraint is grounded in verified `file:line` evidence and every non-code constraint is grounded in its authoritative external source before decomposing boundaries.

---

## 2. System Spine & Macro Axis Gate

1. **System Spine Scoping**: **When** decomposing the system before dispatching any boundary, evaluate each architectural decision or invariant in scope individually while holding the rest fixed: place a decision in the System Spine (recorded in `dag-v1.md` and injected into every `task.md`) whenever two or more boundaries depend on a shared resolution of it so choosing independently would force rework or split the system into inconsistent standards; leave every decision whose effect stays inside one boundary to that boundary's crafter. Construct the System Spine strictly from the decisions ruled cross-boundary.
2. **Coexistence Constraint Check**: **When** the system's transition from its current state to its target state requires a coexistence period because dependent actors or systems cannot cut over simultaneously, record that coexistence constraint explicitly in the System Spine so affected boundaries isolate temporary bridging mechanisms into `Transition Seam` rather than `Target Contract`.
3. **Macro Axis Gate**: **When** finalizing the System Spine before dispatching any boundary, evaluate each Spine decision individually while holding the rest fixed: proceed directly into DAG dispatch whenever the dispatch context and governing invariants settle every Spine decision to one valid direction; pause and escalate through the Main Agent whenever at least one Spine decision remains unsettled and admits two or more valid system strategies whose choice depends on an external priority not stated in the dispatch context. While awaiting the user's ruling, keep this `Architecture Orchestrator` subagent alive so the Main Agent delivers the ruling back via `send_message` and you record the settled Spine and resume without repeating Reality Mapping.

- **Completion Criterion**: Every cross-boundary decision is ruled into the System Spine and settled (by dispatch context, governing invariants, or user ruling via `send_message`).

---

## 3. Boundary Decomposition & DAG Construction

Partition the system into isolated boundary nodes, wire their contract dependencies into a Directed Acyclic Graph, and write the specification to `.gtd/<task-name>/dag-v1.md`.

### Generative Principle
A boundary encapsulates a design decision that is likely to change, hiding its complexity behind a simple interface.

Decompose the system mechanically by applying three invariant operations:
- **Merge**: Components that share internal mutable state or exhibit bidirectional dependencies share the same design decision and must collapse into a single boundary.
- **Split**: Split any component that encapsulates more than one independent design decision.
- **Prune**: Reject any boundary whose interface is as complex as its implementation.

### Physical Graph Contract
Write `.gtd/<task-name>/dag-v1.md` containing:
1. `## System Spine`: Every settled cross-boundary decision, shared invariant, active domain-reference invariant, and any mandatory coexistence constraint.
2. `## Boundary DAG` (in topological order): For every boundary node, specify:
   - `boundary_name`: Unique kebab-case boundary identifier slug.
   - `capability`: The observable outcome this boundary enables for external actors or downstream boundaries, defined strictly by what it makes possible rather than how it operates.
   - `starting_points`: Verified existing codebase anchors for this boundary (empty `[]` when no prior code constrains it).
   - `external_anchors`: Authoritative external, dispatch, or platform constraints anchoring non-code parts of this boundary (`None` when all constraints reside in existing code).
   - `dependencies`: Direct upstream boundary identifiers whose exported contracts this boundary depends on.

- **Completion Criterion**: `.gtd/<task-name>/dag-v1.md` contains the settled System Spine and a strictly acyclic topological boundary graph where every boundary is grounded in its per-element anchors.

---

## 4. DAG Execution, Bounded Negotiation & Escalation

Execute boundaries strictly by topological dependencies defined in the active `.gtd/<task-name>/dag-v<N>.md`. Dispatch a boundary node if and only if every upstream dependency has delivered its exported `contract.md`.

For each eligible boundary node:
1. Write the task dispatch file to `.gtd/<task-name>/<boundary_name>/task.md` matching this physical contract:
   ```markdown
   # Task Dispatch: <boundary_name>

   ## 1. Capability
   <The observable outcome this boundary enables for external actors or downstream boundaries>

   ## 2. System Spine
   <Verbatim settled System Spine from active dag-v<N>.md>

   ## 3. Upstream Contracts
   - [.gtd/<task-name>/<dep>/contract.md](file://...) <!-- or "None" for root nodes -->

   ## 4. Anchors & Context
   - Dispatch: [.gtd/<task-name>/communicate/dispatch_orchestrator.md](file://...)
   - Starting Points (non-exhaustive verified existing code anchors; Boundary Crafter must still trace all affected files within this boundary):
     - [<path/to/file>](file://...) <!-- verified existing code anchors, or "None" -->
   - External Anchors:
     - <Authoritative external/platform constraints, or "None">

   ## 5. Deliverables
   - Final Proposal: `.gtd/<task-name>/<boundary_name>/proposal.md`
   - Exported Contract: `.gtd/<task-name>/<boundary_name>/contract.md`
   ```
2. Resolve the absolute path to `boundary_crafter_instructions.md` located in the same directory as this instructions file (`dirname`) without reading it into Orchestrator context. Spawn a new `self` subagent with role `Boundary Crafter` using this invocation prompt:
   `Execute boundary architecture according to instructions at <boundary_crafter_instructions_path> using task context from .gtd/<task-name>/<boundary_name>/task.md`
3. Handle the Boundary Crafter's response according to its outcome:
   - **Completed**: Inspect the delivered `proposal.md` and `contract.md` to verify whether remaining unexecuted boundaries require adjustment. If adjustments are required, write `.gtd/<task-name>/dag-v<N+1>.md` copying all unaffected boundaries and fields verbatim from version `N` with zero drift before dispatching subsequent nodes.
   - **`CONTRACT_CHANGE_REQUEST`**: **When** the Orchestrator receives a `CONTRACT_CHANGE_REQUEST` within an upstream boundary's one-revision limit and confirms that absorbing the requested change into the upstream boundary reduces complexity outside that upstream boundary without introducing a cycle, write `.gtd/<task-name>/dag-v<N+1>.md` recording the upstream adjustment, re-dispatch the upstream boundary to emit its revised `contract.md` and `proposal.md`, and re-run every already-completed boundary that relies on any modified clause of that revised contract before continuing downstream. Once an upstream boundary has exhausted its one-revision limit, escalate any remaining unresolvable conflict via `CIRCUIT_BREAKER_TRIGGERED`.
   - **`HUMAN_DECISION_REQUIRED`**: Relay the unsettled external priority, each competing candidate's concrete consequences, and any artifact link to the Main Agent while keeping both this Orchestrator and the paused `Boundary Crafter` alive. Once the Main Agent returns the user's ruling via `send_message`, forward that ruling via `send_message` to the paused `Boundary Crafter` so it finalizes `proposal.md` and `contract.md`.
   - **`CIRCUIT_BREAKER_TRIGGERED`**: Package the contradiction summary, physical evidence, and artifact link, send an escalation message to the Main Agent, and stop until human resolution arrives.

- **Completion Criterion**: Every boundary node in the active `dag-v<N>.md` has delivered a verified `proposal.md` and `contract.md` with zero stale downstream dependencies.

---

## 5. System Synthesis

Upon completion of all boundary nodes, author `.gtd/<task-name>/architectural_proposal.md` as an executive system blueprint readable in under five minutes without duplicating individual proposals or contracts:
1. **System Spine & Settled Macro Decisions**: Summary of cross-boundary invariants and any Macro Gate rulings.
2. **End-to-End Architecture & Dataflow**: How capabilities compose across the boundary DAG from entry to exit boundaries.
3. **Boundary Deliverables Index**: Topological list linking each boundary's `proposal.md` and `contract.md`, ordered as the handoff sequence for downstream `boundary-plan` execution.
4. **Consolidated Decision Log**: Key adjudicated trade-offs, rejected alternatives, human rulings, and any accepted `CONTRACT_CHANGE_REQUEST` revisions across boundaries.
5. **Transition Seams Index** *(include only when at least one boundary declares a `Transition Seam`)*: Each temporary bridging seam, its compatibility scope, and its observable `sunset trigger`.

Record completion in `.gtd/<task-name>/communicate/orchestrator_complete.md` and report the clickable link to `.gtd/<task-name>/architectural_proposal.md` to the Main Agent.

- **Completion Criterion**: `.gtd/<task-name>/architectural_proposal.md` and `.gtd/<task-name>/communicate/orchestrator_complete.md` are written and the final link is reported to the Main Agent.
