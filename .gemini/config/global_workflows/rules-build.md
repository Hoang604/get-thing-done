---
name: rules-build
descrition: Rules that let the agent build production code
---
## IMPLEMENTATION FRICTION & DEFENSIVE ARCHITECTURE

System must survive physical execution constraints. Force defensive boundaries.

### 1. State Space & Temporal Chaos
- **Race Conditions (Actor Model / Messages):** No shared mutable memory. Isolate state. Serialize mutations via queues/channels.
- **State Complexity (ADTs):** No implicit variables or boolean flags. Use Algebraic Data Types (ADTs) or strictly typed Tagged Unions. Invalid states must be structurally unrepresentable (Total = A+B).

### 2. Physical Limits & Mechanical Sympathy
- **Backpressure / Traffic Shaping:** Bounded queues only. Internal: Reactive Pull (Demand Signaling). External: Traffic Shaping (Token Bucket: capacity b, refill rate r, HTTP 429).
- **Circuit Breakers & Bulkheads:** Wrap cross-boundary I/O in Circuit Breakers (fast-fail on latency). Use Bulkheads (dedicated connection pools per service) to isolate failures.
- **Abstraction Boundaries / Leaky Abstractions:** Map boundaries to physical failure domains and transactional limits. Expect RPC/ORM mechanical leaks (N+1, latency). Design defensively against leaks.
- **Mechanical Slack:** No brittle, hyper-precise paths. Engineer slack: Shock absorbers, latency fallbacks, graceful degradation.

### 3. Zero-Trust Contracts (Byzantine Faults)
- **Zero-Trust Boundaries (Parse, Don't Validate):** Avoid primitives (String, Int) post-ingestion. Use Design by Contract (Preconditions/Postconditions). Fail-Fast immediately on invalid input.
- **Crash-Only / Fail-Fast:** No complex error recovery for invalid states. Crash isolated component immediately. Micro-Reboot from clean state.

### 4. Stateful Durability & Forensic Observability
- **Stateful Durability:** Separate compute from state. Message brokers / event logs. At-Least-Once Delivery with explicit ACKs post-persistence.
- **Forensic Observability:** Context propagation. Pass Trace ID everywhere. Log Trace ID before Fail-Fast. Route poison payloads to Dead Letter Queue (DLQ) after retry limit (N).

---

## CODE GENERATION & SYNCHRONIZATION

For I/O, Concurrency, or large transformation logic, include `[Cognitive Sync]`:
1. **Big-O Complexity:** Time/space.
2. **Abstraction Leaks:** Physical risks (GC, Deadlocks, File Descriptors).
3. **Metastable Failure Triggers:** Load threshold for unrecoverable collapse.
4. **Anti "Vibe-Coding" (Somatic):** Explicit Semantic Gap. What costs (memory/latency) are hidden by this abstraction?
5. **Per-Block MTTU:** On-call engineer diagnosis time.

---

## COMPLEXITY BUDGET & MTTU

MTTU (Mean Time to Understanding) is first-class constraint. Maximize incident diagnostic speed.

1. **MTTU Design Constraint:** Evaluate against 3 AM on-call developer understanding speed. Reject complex code.
2. **Complexity Budget:** Minimize new dependencies, services, or layers. Flat, observable structures > deep pure abstractions.
3. **Write-Only Code Prevention:** Max ~200 lines of novel logic per response. Deliver in chunks. Confirm understanding before next.
