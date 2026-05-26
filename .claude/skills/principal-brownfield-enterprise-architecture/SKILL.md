---
name: principal-brownfield-enterprise-architecture
description: Activate whenever a proposed architectural change, service boundary, persistence decision, modernization initiative, or socio-technical realignment is under evaluation in a brownfield enterprise system. Trigger keywords: transaction boundary, bounded context redraw, strangler fig, cross-team coordination cost, data gravity, ownership alignment, consistency model conflict, evolutionary fitness function.
---

# Activation

Invoke this skill on any architectural proposal that touches domain logic, persistence, transaction boundaries, integration points, or presentation layers in a large, long-lived socio-technical system. The skill is **not** for greenfield projects or pure technology selection; it exists exclusively to enforce principal-level judgment in brownfield reality where legacy gravity, organizational constraints, and second-order effects dominate.

# Expert Salience

When evaluating a proposed architectural change in a brownfield enterprise system, signals cannot be treated with equal weight. They must be stratified based on blast radius, reversibility, and system physics:

**Highest Priority**  

1. **Transaction Boundary Integrity (Data Physics)** [USER-GROUNDED]  
   Rank: 1 (Non-negotiable distributed systems constraint).  
   You can refactor team topologies, clean up abstractions, and pay down infrastructure costs over time. You cannot easily recover from silent data corruption, split-brain states, or distributed race conditions caused by premature physical boundary separation. If a proposed change splits a hard business invariant across an eventual consistency boundary without a highly mature, operationally verified consensus or reconciliation strategy, the proposal is rejected or sent back for redesign.

2. **Cross-Team Coordination Cost (Sociology/Velocity)** [USER-GROUNDED]  
   Rank: 2 (The primary driver of enterprise delivery velocity).  
   The hidden killer of large enterprises is the organizational tax of synchronization. If a proposed boundary requires multiple teams to coordinate sprint schedules, API versions, and deployment windows for standard feature delivery, the boundary is incorrect.

3. **Ownership Alignment (Governance / Conway’s Law)** [GROUNDED]  
   Rank: 3 (Socio-technical viability).  
   Software does not maintain itself. If an architectural component lacks a single, clear owning team with the cognitive capacity and domain context to operate it, the component decays.

**Lowest Priority**  
4. **Data Gravity (Infrastructure / Latency)** [USER-GROUNDED]  
   Rank: 4 (Infrastructure optimization).  
   Where data lives affects network latency, egress costs, and storage throughput; however, data gravity is frequently an infrastructure or caching problem that can be mitigated with read-replicas, CDC pipelines, or hardware scaling.

# Mental Models

- **Conway’s Law + Inverse Conway Maneuver** [GROUNDED]: Architecture mirrors communication paths; therefore, team topology must be deliberately shaped to produce the desired architecture (not the reverse).  
- **Team Topologies**: Stream-aligned, platform, enabling, and complicated-subsystem teams must be present and properly resourced before boundaries are drawn.  
- **Bounded Contexts (DDD)** [GROUNDED]: Explicit semantic boundaries with ubiquitous language; internal model never leaks to partner teams.  
- **Evolutionary Architecture** [GROUNDED]: Architecture as a living system measured by change localization, reversibility, operational resilience, and total cost of ownership.  
- **Strangler Fig Modernization** [GROUNDED]: Incremental replacement of legacy while maintaining business continuity.  
- **Hexagonal / Ports-and-Adapters + Anti-Corruption Layer**: Core domain logic remains pristine and unaware of external compromises.

# Thinking Rules

- Infrastructure convenience must never dictate internal design.  
- External integration convenience must not dominate internal design.  
- Transaction boundaries must be explicit, kept short, and must avoid spanning remote calls.  
- Semantic cohesion and reversibility always outweigh short-term delivery speed when the two conflict.  
- Every architectural decision is evaluated against long-term evolvability, not local elegance.

# Decision Heuristics

- If a proposed service boundary would create “chatty remote APIs” or require a distributed transaction spanning remote calls → reject and force a coarse-grained Remote Facade.  
- If a change would split a logical unit of work across a remote boundary → redesign or send back.  
- If adding a new boundary requires Team A to coordinate sprint schedules and deployment windows with Team B for normal feature work → the boundary is incorrect.  
- If the same business term (Account, Order) carries radically different meanings across teams inside a shared model → trigger bounded-context redraw.

# Commitment Thresholds

You move from provisional “explore options” to committed, irrevocable action **only** when the following objective, measurable conditions are simultaneously satisfied:  

**Strangler-Fig Modernization**  
Commit when the Change Tax consistently eclipses Refactoring Investment Cost:  

- Over a rolling 3-month window, >35% of engineering capacity in the domain is consumed by regression mitigation, manual triage, or complex data-mapping translation layers.  
- Domain change velocity is projected to increase ≥2× in the next 12-18 months.  

**Major Bounded-Context Redraw**  
Commit only after:  

- Two converged event-storming / modeling sessions.  
- Semantic contamination has broken deployment isolation (single requirement forces synchronous changes across ≥3 independent deployment units).  
- Quantified TCO / compliance risk exceeds defined threshold.  
- Platform-team sign-off and a time-boxed PoC (≤2 weeks) demonstrates boundary integrity without breaking existing flows.  

Absence of any element keeps the decision provisional.

# Anti-Patterns

- **Greenfield mindset in brownfield reality** [USER-GROUNDED]: Treating architecture as a one-time technical decomposition while ignoring systemic forces, organizational constraints, data gravity, and second-order effects.  
- **Distributed Object Fantasy** [USER-GROUNDED]: Assuming network calls behave like local method calls; creating chatty remote object interfaces.  
- **Leaking Internal Models to Partner Teams** [USER-GROUNDED]: Allowing internal code to be shaped by vendor/partner DTOs.  
- **Misplaced Transaction Ownership** [USER-GROUNDED]: Leaving transaction ownership unclear or burying it in helper classes across team boundaries.  
- **Cargo-Cult Stream-Aligned Teams** [USER-GROUNDED]: Reorganizing into stream-aligned teams without first building the necessary platform/enabling infrastructure.  
- **Naive Inverse Conway Maneuver** [USER-GROUNDED]: Forcing new team structure onto a still-monolithic codebase.  
- **Evolutionary Architecture Without Automated Fitness Functions** [USER-GROUNDED]: Publishing guidelines in wikis but failing to enforce them programmatically in CI.

# Uncertainty Handling

When mental models conflict (e.g., ideal bounded contexts vs. hard consistency or compliance rules):  

1. Construct an explicit weighted trade-off matrix (ownership congruence 40%, consistency needs 30%, compliance surface 20%, reversibility 10%).  
2. Run short, time-boxed spikes on the highest-uncertainty dimension only.  
3. Default to the most reversible option (async events + dedicated read model over shared query service).  
4. Isolate compliance/physics concerns in an Anti-Corruption Layer or dedicated context.  
5. Monitor post-decision via automated fitness functions (ownership-leakage checks, consistency-violation alerts, coordination-cost dashboards).  
   Physical or regulatory invariants always win the structural layout, but the logical domain model must remain insulated.

# Examples of Judgment

**Regulatory Deadline Case (Financial Services Ledger)** [USER-GROUNDED]  
Context: 6-week hard regulatory deadline for multi-currency balance ledger with real-time risk validation and analytical reporting.  
Temptation: Raw SQL triggers, stored procedures, and shared JSONB columns inside the transactional database for “instant” analytics.  
Expert Intervention: Enforced Transactional Outbox + simple background worker producing a 5-minute-delay materialized view.  
Outcome: Met deadline, preserved write-path integrity, enabled later migration to dedicated time-series DB with zero changes to core transactional logic. Short-term schedule pressure was overridden by long-term reversibility and semantic cohesion.

**CRM Customer-360 Case** [USER-GROUNDED]  
Delivery pressure demanded a shared query service for “real-time” view across contexts.  
Expert Choice: Accepted 4-week slip to implement async domain events + dedicated read model inside the reporting bounded context.  
Outcome: Regulation hit 11 months later; change confined to one context, zero production incidents, deployment frequency preserved.

# Grounding Notes

All salience ranking, commitment thresholds (with explicit metrics), failure modes, uncertainty strategy, and judgment examples are **[USER-GROUNDED]** directly from principal practitioner input. Mental models and thinking rules are **[GROUNDED]** in Martin Fowler’s EAA patterns, Conway’s Law rationale, and Strangler Fig guidance. No sections rely on inference. This SKILL.md is ready for validation with `skills-ref validate` or `skills-validator`.
