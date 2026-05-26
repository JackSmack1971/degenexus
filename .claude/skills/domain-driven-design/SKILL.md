---
name: domain-driven-design
description: Triggered when linguistic friction, repeated conditionals, awkward APIs, temporal mismatches, unclear sources of truth, or subdomain triage decisions appear in code, stakeholder discussions, or event storming. Activates expert discovery of behavior-rich models from business reality using ubiquitous language, bounded contexts, invariant-centered aggregates, and strategic distillation. Prioritizes core-domain leverage; corrects data-structure isomorphism ("Fake DDD").
---

# Activation

Activate this skill the moment any of the following load-bearing signals surface during modeling or implementation:  

- Linguistic friction or contradictory terminology between stakeholders or across code.  
- Repeated conditionals or vague status/type flags flattening business rules.  
- Awkward/verbose APIs or temporal mismatches in entity lifecycles.  
- Subdomain decisions involving core vs supporting/generic classification.  
- Aggregate boundary or strategic distillation questions.  
  [USER-GROUNDED]

# Expert Salience

Load-bearing features (ranked by expert weighting):  

1. **Linguistic friction** (10/10) — hesitation, competing definitions, or awkward naming; signals collapsed or bleeding bounded contexts.  
2. **Invariant density & clustering** (9/10) — what *must* be transactionally consistent together.  
3. **Competitive asymmetry / core-domain leverage** (9/10) — does a change here shift gross margin, retention, or velocity by an order of magnitude?  
4. **Rate of policy mutation** (8/10) — business rules changing due to market forces.  
5. **Repeated conditionals / temporal mismatch** (8/10) — implicit concepts screaming for explicit Value Objects, Policies, or State Machines.  
   Ignore or deprioritize: database tables, UI screens, generic status fields, structural reuse opportunities. These are noise unless they reveal business behavior.  
   [USER-GROUNDED]

# Mental Models

- **Core-Leverage-First Matrix**: Plot subdomains on (strategic differentiation × volatility/change-frequency × invariant density). Rich behavior-rich modeling (supple aggregates, full UL, event orchestration) *only* in high-leverage core cells; supporting/generic cells default to transaction scripts or CRUD.  
- **Competitive Asymmetry Engine**: If an algorithmic or structural change directly moves business metrics by an order of magnitude, it is core and demands zero-compromise modeling.  
- **Rate of Policy Mutation**: High volatility → rich domain model; low volatility + high structural complexity → ACL + off-the-shelf or scripts.  
- **Cognitive Load Boundary**: If engineers constantly translate corporate operations into generic data structures, introduce rich DDD to anchor code to real-world operations.  
- **Strategic Distillation (Evans)**: Core / Supporting / Generic + Anti-Corruption Layers.  
  All models treat the domain model as *discovered* from business behavior, never invented from technical structure.  
  [GROUNDED]

# Thinking Rules

- Models are discovered through knowledge crunching, not invented from DB schemas or UI flows.  
- Ubiquitous Language must be shared and unambiguous inside a bounded context: one concept, one name; one name, one concept.  
- Aggregate boundaries are defined exclusively by business invariants requiring immediate consistency, not by object relationships or ORM convenience.  
- Bounded contexts follow semantic divergence, not opportunities for structural reuse.  
- Rich modeling effort is reserved for the core domain; aggressive simplification is required everywhere else.  
- Working behavior must be preserved while moving toward deeper models in safe, incremental steps.  
  [GROUNDED] [USER-GROUNDED]

# Decision Heuristics

- If linguistic friction or repeated conditionals appear → immediately extract explicit domain concepts (named Policies, Specifications, State Machines) rather than burying rules in comments or flags.  
- If a subdomain shows high competitive asymmetry or policy mutation rate → invest in supple, behavior-rich aggregates and event orchestration.  
- If an aggregate would require >1 DB round-trip or >6 business rules for consistency → split it.  
- When evaluating boundaries: run happy-path + exception-path event storming. If the timeline feels procedural or forces CRUD over business decisions → boundary is wrong.  
  [USER-GROUNDED]

# Commitment Thresholds

A model is declared “discovered” (not invented) and boundaries/roots are finalized only when **all** of the following if/when conditions are simultaneously satisfied:  

- **Zero-Translation Linguistic Threshold**: Business stakeholders can read method signatures, event names, or class names in the code and understand the business logic immediately without any engineer translation.  
- **Open-Closed Stability Threshold**: New business requirements or policy variations can be implemented by *adding* new Value Objects, Domain Events, or Policy strategies rather than changing structural properties of existing Aggregate Roots.  
- **Command Intent Autonomy Threshold**: The model rejects generic mutations (e.g., `updateProfile()`) in favor of clear, intent-driven operations (e.g., `relocatePrimaryResidence()`), and invalid transitions are prevented by the aggregate interface itself.  
- Language convergence across ≥3 stakeholders (<10 % friction) + invariant clustering workshop complete + Competing Model Test passed on the same scenarios.  

**If any threshold fails** → remain provisional, log assumptions with “if-wrong” triggers, and continue knowledge crunching / event storming.  
[USER-GROUNDED]

# Anti-Patterns

- **Fake DDD / Data-Structure Isomorphism**: Modeling around database tables, UI screens, generic status fields, or tactical pattern ceremony instead of business state transitions.  
- **God Aggregate / Gravitational Entity**: Large graph aggregates optimized for ORM convenience instead of atomic transactional invariants (causes lock contention and memory bloat).  
- **Distillation Blindness**: Spending equal modeling effort on every subsystem or letting technical mechanisms dominate the core model.  
- **Upstream Bi-Directional Contamination**: Cyclical dependencies between bounded contexts without proper Anti-Corruption Layers.  
- **Anemic Event Choreography**: Fine-grained property-change events instead of intent-driven behavioral events.  
- Treating any first model as final (contradicts knowledge-crunching stance).  
  [GROUNDED] [USER-GROUNDED]

# Uncertainty Handling

- **Model Plurality**: Maintain 2–3 competing models as hypotheses until evidence converges; never force-fit a compromise abstraction.  
- **Dual-Model Separation Principle**: When experts disagree on a concept (e.g., “Customer”, “Qualified Lead”), model them separately in different bounded contexts with explicit translation at the boundaries.  
- **Temporal Forking**: When state transitions are ambiguous, shift focus to the passage of time and introduce explicit negotiation or tracking aggregates (e.g., ProposedPolicyNegotiation).  
- **Empirical Deferment**: For high ambiguity, start with a simple append-only event log + lightweight transaction script; let real operational events reveal true boundaries before committing to rigid entities.  
- Treat every linguistic friction or expert disagreement as gold — run collaborative specification workshops with concrete examples and “what-if” scenarios.  
  [USER-GROUNDED]

# Examples of Judgment

**Scenario 1 (Signal Weighting)**: Repeated `if (status == "PENDING")` blocks appear. Expert weights this 8/10 → extracts explicit `OrderPending`, `OrderApproved`, `OrderRejected` Value Objects or a State Machine, even though it adds classes, because it eliminates conditionals and makes policy explicit. Provisional acceptance only after UL convergence >85 %.  

**Scenario 2 (Boundary Decision)**: Proposal to put User preferences and Billing inside one Account aggregate. Expert runs invariant analysis: “Does updating preferences block invoice processing in the same transaction?” → No → immediate split. Saves future lock contention.  

**Scenario 3 (Uncertainty)**: Sales and Risk disagree on “Qualified Lead”. Expert applies Dual-Model Separation: creates `SalesPipelineContext::Lead` and `RiskEvaluationContext::Prospect` with asynchronous mapping rather than a single compromised object.  

**Scenario 4 (Commitment)**: After workshops, stakeholders spontaneously use model terms unprompted and new requirements are satisfied by adding strategies without touching Aggregate Roots → thresholds met → model declared discovered.  
[USER-GROUNDED]

# Grounding Notes

All content is [USER-GROUNDED] from the provided DDD expertise stance and detailed answers to the five clarifying questions, cross-anchored to Evans strategic distillation, Fowler bounded-context principles, and Vernon aggregate consistency guidance. No inference used. Grounding quality STRONG. To strengthen further, paste additional design rationale or event-storming examples.
