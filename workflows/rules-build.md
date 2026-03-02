---
name: rules-build
descrition: Rules that let the agent build production code
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
5. **Per-Block MTTU Estimate:** For this specific code block, how long would it take an unfamiliar on-call engineer to understand it well enough to diagnose a failure? Flag if this exceeds a reasonable threshold for the component's criticality.

## COMPLEXITY BUDGET & MEAN TIME TO UNDERSTANDING (MTTU)

**The Context:** AI generation bandwidth is effectively infinite. The load-bearing constraint on system survivability is no longer how fast code is written, but how fast a human can understand it during a 3 AM incident. A solution that ships in 4 hours but takes 3 days to comprehend during an outage is "Bad Velocity" — it creates negative architectural value.

**1. MTTU as a First-Class Design Constraint:**
When proposing any architectural design or implementation, you MUST evaluate it against Mean Time to Understanding: "If this component fails at 3 AM and an on-call engineer who did not write it must diagnose the failure, how long will it take them to understand what this code does and where to intervene?" If the answer exceeds the tolerance for the component's criticality, the solution is rejected regardless of its theoretical elegance.

**2. Anti-Complexity Sprawl (Local Optimization Trap):**
You MUST NOT act as a "Local Optimizer" — solving a specific ticket by introducing excessive new dependencies, services, abstraction layers, or state machines. Before introducing ANY new dependency or architectural component, you MUST justify it against the Complexity Budget:
- Does this new component increase the global MTTU?
- Can the requirement be satisfied by extending an existing component?
- Is the added complexity proportional to the blast radius of the problem being solved?

If a simpler solution exists that is 80% as elegant but 50% more comprehensible, you MUST prefer the comprehensible solution. Favor **flat, observable, debuggable** structures over **deep, layered, theoretically pure** abstractions.

**3. Write-Only Code Prevention:**
You MUST NOT generate code faster than it can be comprehended. If a single response generates more than ~200 lines of novel logic (not boilerplate/config), you MUST break the delivery into comprehensible chunks, each with its own `[Cognitive Sync]` block. The user must confirm understanding of chunk N before chunk N+1 is delivered.
