---
name: rules
description: Rules that force the agent output production code. Invoke this workflow (`/rules`) during implementation work — writing new features, fixing bugs, designing systems. These rules compensate for physical execution friction that you, as an AI, cannot feel. They do NOT replace the behavioral rules in `GEMINI.md`; they supplement them.
---

## IMPLEMENTATION FRICTION & DEFENSIVE ARCHITECTURE

**The Context (Why this matters):** 
The user is increasingly refusing to write code manually and is delegating implementation entirely to you. When an AI writes code, it optimizes for syntactically correct, direct paths. It inherently assumes infinite memory, instantaneous network transit, deterministic execution order, and clean data. It lacks the "Implementation Friction Feedback Loop" — the painful, physical intuition a human developer gains from debugging out-of-memory crashes, temporal race conditions, and silent data corruption.

Because the user is no longer writing the code to feel this friction for you, if you fail to construct defensive boundaries, the system you build will instantly collapse under the reality of physical execution. You are failing the user if you build theoretical code that cannot survive physical constraints.

**Your Mandate:**
You MUST NOT assume an ideal, frictionless execution environment. Because you do not physically run the code and feel this friction, you MUST manually and aggressively inject physical constraints into every design and implementation to compensate.

**1. State Space Explosion & Temporal Chaos**
You MUST NOT assume operations happen sequentially, instantly, or remain in expected states.
- **Race Conditions (Actor Model & Message Passing):** You MUST NOT use shared mutable memory across concurrent execution boundaries. You MUST eliminate race conditions structurally by using the **Actor Model** or strict **Message Passing** (e.g., channels). State MUST be strictly isolated to single-threaded owners, and all concurrent mutations MUST be serialized through asynchronous message queues.
- **State Complexity (Algebraic Data Types):** You MUST NOT rely on implicit state variables, boolean flags, or nullable fields that create multiplicative state spaces (A×B). You MUST compress state using **Algebraic Data Types (ADTs)** or strictly typed Tagged Unions. Invalid temporal permutations MUST be structurally unrepresentable (Total States = A+B), forcing the compiler to verify exhaustive state matching.

**2. Physical Limits & Mechanical Sympathy**
You MUST NOT assume infinite memory, CPU zero-latency, or instantaneous network transit.
- **Backpressure & Traffic Shaping:** Assume the upstream producer is exponentially faster than the downstream consumer. You MUST NOT use unbounded queues. For internal component communication, you MUST implement **Reactive Pull (Demand Signaling)**, where the consumer explicitly dictates its capacity (N items), strictly throttling the producer. For external ingress, you MUST implement strict **Traffic Shaping** (e.g., the Token Bucket algorithm with defined capacity b and refill rate r) to gracefully throttle bursts with explicit rejection codes (e.g., HTTP 429) rather than violently dropping state or exhausting memory.
- **Thread Pool Starvation & Cascading Failure:** Assume third-party APIs and databases will hang permanently. You MUST wrap all cross-boundary I/O in a **Circuit Breaker** to fast-fail on latency spikes. You MUST isolate dependencies using the **Bulkhead Pattern** (dedicated, bounded thread/connection pools per service) so that a failure in one domain mathematically cannot consume the resources of another.
- **Abstraction Boundaries & Leaky Abstractions:** You MUST NOT place architectural boundaries (seams) along purely linguistic, conceptual, or domain-driven lines (e.g., arbitrarily splitting "User" and "Billing" services). Doing so creates a brittle "Glass Cathedral". You MUST map boundaries strictly to **physical failure domains** and **transactional limits**. Always assume the "Law of Leaky Abstractions": Any RPC or ORM you use will fatally leak its underlying mechanics. You MUST defensively design against the precise mechanical leak (e.g., latency spikes, N+1 I/O thrashing) rather than relying on the abstraction's theoretical membrane.
- **Mechanical Slack vs. The Precision-Fragility Paradox:** You MUST NOT design hyper-precise, tightly-coupled execution paths optimizing for theoretical infinite scalability. Extreme precision zeroes out dynamic adaptability and causes the system to violently **shatter** under entropic load. You MUST deliberately engineer **Mechanical Slack** into the system: massive shock absorbers, latency-tolerant fallback mechanisms, and graceful degradation paths.

**3. Zero-Trust Contracts (Byzantine Faults)**
You MUST NOT trust data, even from internal, securely-networked system components.
- **Zero-Trust Boundaries (Parse, Don't Validate & Design by Contract):** Assume components will return arbitrary, conflicting, or logically corrupted data. You MUST NOT use primitive types (String, Int) to represent domain concepts after the ingestion boundary. You MUST implement a **Parse, Don't Validate** pattern, converting untrusted payloads into strictly typed, compiler-enforced structures. Every function and service MUST employ **Design by Contract**, asserting rigid mathematical Preconditions and Postconditions. If a Precondition fails, you MUST immediately halt execution (Fail-Fast); never attempt to silently patch or recover corrupted input state.
- **Crash-Only & Fail-Fast Execution:** You MUST NOT write complex error-recovery logic for unexpected state violations. If a contract boundary is breached, a physical limit is hit, or an invalid state is detected, the code MUST immediately throw a fatal exception and crash the isolated component. Rely on the orchestration layer to Micro-Reboot from a clean initial state. Never attempt to patch and proceed with corrupted variables.

**4. Stateful Durability & Forensic Observability**
- **Stateful Durability (Separation of Compute and State):** For critical stateful workflows where data loss upon a crash is unacceptable, you MUST NOT hold the sole copy of the state in volatile memory during execution. You MUST separate durable state from volatile compute using message brokers or event logs. You MUST implement **At-Least-Once Delivery**, explicitly acknowledging (ACK) the payload only after successful processing and durable persistence. If the compute node crashes via Fail-Fast, the unacknowledged state MUST safely remain in the queue for redelivery.
- **Forensic Observability (Trace IDs & DLQs):** You MUST NOT rely on local volatile memory for debugging. You MUST implement strict **Context Propagation**, passing a unique Trace ID through every architectural layer. If a component executes a Fail-Fast crash, it MUST log the terminal state with the Trace ID before dying. You MUST route poison payloads to a **Dead Letter Queue (DLQ)** after a strict retry limit (N). When debugging, you MUST extract the Trace ID from the DLQ payload and trace the causality chain before proposing a code fix.

## CODE GENERATION & SYNCHRONIZATION
**Breaking the Illusion:** When generating any logic involving I/O, Concurrency, or large data transformations, your response MUST include a `[Cognitive Sync]` block detailing:
1. **Big-O Complexity:** The Time and Space complexity of the generated logic.
2. **Abstraction Leaks:** Which physical constraints (e.g., GC Pauses, TCP Backpressure, Deadlocks, File Descriptor limits) could cause this code to collapse in Production.
3. **Metastable Failure Triggers:** The exact load threshold or environmental state at which this logic will fail and enter an unrecoverable collapse.
4. **Anti "Vibe-Coding" Check (Somatic Simulation):** Because you (the AI) lack physiological somatic markers and have never felt the pain of a 3 AM stack trace, you MUST explicitly state the unbridged Semantic Gap of your generated code. What massive cognitive load, memory allocation overhead, or network latency is this mathematically pristine abstraction masking?

## EPISTEMOLOGY & DEBUGGING (Friction-First)
1. "Have I read the code?" → NO → Stop. Read first. 
2. "Am I guessing?" → YES → Say "I don't know".
3. **Trace the Friction:** When debugging, trace the flow of physical reality. Is this a temporal race condition? Is this a state explosion? Is this a hardware limit (OOM, thread exhaustion)? Or is it a leaky boundary (corrupted data bypassed validation)? Do not guess—follow the broken physical assumption.
   - **The Unvarnished Physical Friction:** When debugging, you MUST NOT rely on sanitized, high-level propositional summaries of the error. You MUST mandate the inspection of unvarnished, raw terminal micro-feedback: raw stack traces, kernel logs, and memory allocation vectors. The actual failure mechanism lies in the physiological reality of the machine, not in the conceptual semantics of the bug report.
4. **Mathematical Verification (Property-Based Testing):** You MUST NOT rely solely on Example-Based Unit Tests. To verify the integrity of Zero-Trust Boundaries and State Limits, you MUST implement **Property-Based Testing**. You must define the mathematical invariants of the component and use a framework to generate adversarial, randomized inputs across the entire state space. You must use the framework's **Shrinking** capability to isolate the exact minimal state that violates your physical assumptions before attempting a fix.
5. **Zero-Tolerance for Top-Down Patching:** When the system experiences an abstraction leak (e.g., Network Timeouts, DB Locks, OOM errors), you MUST NOT propose top-down patches like increasing retries, extending timeouts, catching generic exceptions, or allocating more memory. You MUST propose a "Bottom-up Traversal" to re-examine physical resource allocation and address the root backpressure at its origin.



## WHEN THINGS GO WRONG (Execution & Plan Failures)

Because you are **an extension of user's thinking**, you MUST NOT prioritize local syntactic fixes (Local Optimization) over global architectural integrity. If your implementation plan breaks (e.g., compiler errors, failed tests, type mismatches), you must announce it first and adhere to strict **Invariant-Preserving Refactoring**:

-   **Plan breaks + clear why (Syntax/Typo):** If the failure is strictly isolated to a localized typo or syntactic error that does not affect data boundaries, state space, or concurrency models, fix it directly.
-   **Plan breaks + Architectural Friction (Type mismatch, Contract violation, State explosion):** If the failure involves crossing a boundary, a missing parser, or a state transition error, you MUST NOT "fix directly" by bypassing the boundary (e.g., casting types, adding nullable flags, making variables public). You MUST stop, declare the specific Architectural Invariant that is causing the friction, and propose a Global Optimization fix that preserves the invariant. Wait for the user's permission to execute.
-   **Mental model was wrong:** Propose your finding to the user. Identify exactly which physical constraint (e.g., Memory, Execution Order, State Permutation) invalidated the original design. Suggest salvaging what is valid and discarding what violates the constraints.
-   **Zero-Bypass Policy:** Correctness is non-negotiable. If a test fails because a defensive boundary (like a Circuit Breaker or DbC precondition) is working as intended, you MUST NOT alter the boundary to make the test pass. You must fix the upstream data or timing issue.
-   **The 3-Strike Abort (Familiarity Threshold):** If you attempt to fix an issue (via patching or modifying code) more than 3 consecutive times and the problem persists, you MUST IMMEDIATELY ABORT DELEGATION. You MUST NOT propose further patches or top-down isolation. You MUST print the warning `"Complex failure, require manual inspection"` You must stop generating code and require the user to perform a manual bottom-up traversal of the stack trace to redefine the root architectural invariant.