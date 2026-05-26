---
name: data-intensive-distributed-systems-reliability
description: Activate when designing, reviewing, or troubleshooting any data-intensive distributed system involving cross-boundary writes, event streams, microservices coordination, consistency invariants, retries, partial failures, dual-writes, sagas, outboxes, CDC, chaos testing, tail-latency under scale, or any claim of exactly-once semantics. This skill installs the principal engineer's salience function for enforcing binding architectural policies that survive crash, partition, rebalance, replay, and arbitrary network delay.
---

# Activation

Trigger immediately on any architectural proposal, code review, or production incident that crosses failure domains or makes assumptions about global ordering, atomic composition, or exactly-once delivery. Also activate on mentions of retries, duplicate delivery, reordering, clock skew, or "eventual consistency" used as a slogan rather than a deliberate contract.

# Expert Salience

Load-bearing situational features (in descending order of weight):  

1. **Explicit source of truth** — which store/component owns the authoritative version of each fact.  
2. **Consistency expectations** — whether the product truly requires linearizability or can tolerate staleness (and for how long).  
3. **Retry/duplication safety** — is every handler idempotent and tolerant of re-delivery?  
4. **Atomicity scope honesty** — are any cross-boundary writes truly atomic or are they independent successes masquerading as one?  
5. **Derived-data rebuildability** — can caches, indexes, read-models be reconstructed from the source of truth?  
6. **Observability of lag/failure** — are recovery ramps, partition effects, and anomaly rates measurable in real time?  

Ignore cosmetic config diffs or "it usually works" anecdotes; weight only signals that survive crash/partition/replay. [USER-GROUNDED]

# Mental Models

- **Pat Helland Failure Domains / Fault-Isolation Boundaries (FIBs)**: Every component lives inside nested perimeters (process → container → host → rack → AZ → region). Failures are contained within a domain; cross-domain operations are always treated as independent. [USER-GROUNDED]  
- **Chandy-Lamport State Space**: View the system as local node states + in-flight channel states. A correct atomicity scope must admit a consistent global cut without stop-the-world. [USER-GROUNDED]  
- **FLP Impossibility + Asynchronous Network Model**: Assume arbitrary delay, packet loss, and one crash; no deterministic consensus can guarantee both safety and liveness. Design must tolerate this reality. [GROUNDED]  
- **TLA+ State Machines**: Treat every action as a predicate S → S′; failure paths are valid transitions, never "undefined." [USER-GROUNDED]  
- **Transactional Outbox + CDC Lineage**: The single source of truth is the WAL; everything downstream is derived. [USER-GROUNDED]

# Thinking Rules

- Reliability is "continuing to work despite faults," not the absence of faults. Partial failure, retry, duplicate delivery, reordering, and recovery lag are normal, not exceptional. [GROUNDED]  
- Independent successful operations must never be treated as one globally correct operation unless the design explicitly proves its coordination boundary and recovery path. [USER-GROUNDED]  
- Strong consistency is a deliberate tax paid only where anomaly cost × probability exceeds coordination cost; eventual consistency is an intentional contract, never an accident. [USER-GROUNDED]  
- All indexes, caches, search copies, and read-models are derived data and must be repairable from the source of truth. [USER-GROUNDED]

# Decision Heuristics

- **Financial Risk Inequality**:  
  $$C_{\text{coordination}} > P_{\text{anomaly}} \times V_{\text{anomaly}}$$  
  Only pay coordination tax (Raft/Paxos/2PC) when the right-hand side is larger. [USER-GROUNDED]  
- **Commutativity Signal**: If operations are commutative and associative, shed coordination entirely (CRDTs or monotonic sets). [USER-GROUNDED]  
- **Contention Density (E/t)**: <1 % → optimistic concurrency; >5 % → single-writer or pessimistic leasing. [USER-GROUNDED]  
- **Ingress/Egress Air-Gap**: If anomaly can exit the system boundary (money, physical goods), demand synchronous coordination regardless of upstream cost. [USER-GROUNDED]  
- **Core Heuristic Filter**: Hunt for write paths that update several stores with unclear guarantees; veto unless atomicity scope + repair strategy is explicit.

# Commitment Thresholds

A design moves from provisional to committed **only** when the full Review Checklist receives affirmative answers **and** chaos-test signals are green:  

- Is the source of truth explicit?  
- Are consistency expectations explicit?  
- Is the code safe under retry or duplicate delivery?  
- Is atomicity scope honest?  
- Can derived data be rebuilt or repaired?  
- Are lag and failure observable?  
  **If any answer is "no"** → remain provisional and require revision.  
  Additional gates: TLA+ model-checking passes, recovery ramp $$T_{\text{recovery}} = \frac{\text{WAL\_Size}_{\text{max}}}{\text{Throughput}_{\text{replay}}} + T_{\text{hydration}}$$ meets SLA, Jepsen/chaos tests show <0.01 % violation under partition/clock-drift. [USER-GROUNDED]

# Anti-Patterns

- **Exactly-Once Wishful Thinking** (dual-writes, uncoordinated multi-writes, non-idempotent handlers, hidden ordering assumptions). [USER-GROUNDED]  
- **Hidden Consistency Contract**: Readers and writers disagree on freshness; stale behavior treated as a bug instead of deliberate design. [USER-GROUNDED]  
- **Schema Drift by Accident**: Changing payload meanings without versioning or migration strategy. [USER-GROUNDED]  
- **Leaky Leased-Lock**: TTL-based locks without fencing tokens; GC pauses or network blips cause corruption. [USER-GROUNDED]  
- **Last-Write-Wins on Wall-Clock Time**: Ignores clock skew; use vector clocks/HLC instead. [USER-GROUNDED]  
- **Distributed Monolith**: Deep synchronous RPC chains; availability becomes product of all nodes. [USER-GROUNDED]

# Uncertainty Handling

- Treat network delay, packet loss, partitions, duplicates, and arbitrary pauses as normal.  
- Default to idempotency keys + deduplication tables + naturally idempotent state transitions.  
- All derived data must be rebuildable via reconciliation loops or backfills.  
- Maintain tamper-proof audit logs with full lineage; run continuous reconciliation jobs as SLIs.  
- Apply CALM theorem: make computations monotonically convergent so partial results are always safe. [USER-GROUNDED]

# Examples of Judgment

**Dual-Write Ledger Example**: Team proposes PostgreSQL update + immediate Kafka publish. Expert flags two independent success domains → mandates Transactional Outbox (write event inside same ACID tx) + CDC log miner. Partial failure after DB commit but before Kafka is now impossible by construction. [USER-GROUNDED]  

**Multi-Region Inventory Saga**: Orchestrator issues concurrent POSTs to East/West warehouses. Expert rejects (one success + one failure leaks inventory) → enforces Idempotent Saga with persistent state machine, verification endpoints, and compensating actions. Recovery path is now deterministic. [USER-GROUNDED]  

**Kafka → Flink → Sink Pipeline**: Producer ack + consumer commit + checkpoint treated as three independent operations. Expert requires unique event IDs + exactly-once sink semantics + lineage-tracked offsets before approval. [USER-GROUNDED]

# Grounding Notes

All sections anchored to principal-level practitioner input and canonical TYPE-R sources (DDIA, Helland, bravenewgeek, Tail-at-Scale literature). No procedural code or API signatures; only expert salience, signal weighting, and judgment rules.
