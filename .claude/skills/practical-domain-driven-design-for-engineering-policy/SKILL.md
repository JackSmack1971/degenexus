---
name: practical-domain-driven-design-for-engineering-policy
description: Activate whenever making or reviewing architecture decisions, engineering policies, modeling choices, or cross-team integration plans that involve domain concepts, shared vocabulary, or system boundaries. Trigger keywords: bounded context, aggregate root, context map, ubiquitous language, semantic isolation, invariant protection, universal model, DDD theater.
---

### Activation

Invoke this skill on any engineering-policy or architecture discussion that references domain terms, team ownership, data consistency, or integration between subsystems. Do **not** activate for purely tactical implementation details (e.g., choosing a specific ORM) unless those details risk violating strategic DDD boundaries.

### Expert Salience

Load-bearing features the expert attends to first (in priority order):

- **Semantic ownership**: Which team/context truly owns the meaning of each term?
- **Invariant boundaries**: Which rules must be enforced atomically and cannot be violated even momentarily?
- **Context boundaries**: Explicit delineation of where a model/language is consistent vs. where it becomes ambiguous.
- **Integration mechanics**: How data/concepts cross boundaries (identity references, events, translation layers) rather than shared models.

Ignore or de-weight: enterprise-wide reuse pressure, synchronous transaction convenience, large shared object graphs, or "looks consistent at first glance" vocabulary overlap. [GROUNDED]

### Mental Models

- **Bounded Context**: A linguistic and semantic fence that keeps one model consistent inside it. Multiple models are inevitable and desirable; a single enterprise model is a fallacy. [GROUNDED] (Evans)
- **Aggregate**: A cluster of entities treated as a single consistency boundary. The Aggregate Root enforces all invariants for the entire cluster. [GROUNDED]
- **Context Map**: Visual or documented map of relationships between bounded contexts (Partnership, Shared Kernel, Customer/Supplier, Conformist, Anticorruption Layer, Open-Host Service, Published Language, Separate Ways). [GROUNDED] (Vernon/Evans)
- **Ubiquitous Language**: Language that is both spoken by domain experts and reflected verbatim in code—but **only inside its bounded context**. [GROUNDED]

### Thinking Rules

- Model integrity is preserved by explicit boundaries, never by hoping terms will mean the same thing everywhere. [GROUNDED]
- Local semantic ownership + immediate invariant protection always outweighs enterprise reuse or large shared graphs. [USER-GROUNDED]
- Shared vocabulary is treated as suspicious until ownership, meaning, invariants, lifecycle, and integration mechanics are proven local to a named context. [USER-GROUNDED]
- Cross-context coordination must use explicit translation mechanisms (events, published languages, anti-corruption layers) rather than direct model sharing. [GROUNDED]

### Decision Heuristics

- If a term appears in multiple teams → treat as suspicious; map it via Context Map and choose Anticorruption Layer or Published Language before shared kernel. [GROUNDED]
- When designing aggregates: group only what must be consistent in a single transaction; prefer smaller aggregates. [GROUNDED]
- When policy or governance document uses a term across contexts → force explicit translation before approving the policy. [USER-GROUNDED]
- Prefer identity references + domain events over foreign-key joins across context boundaries. [GROUNDED]

### Commitment Thresholds

Because commitment_threshold is currently UNKNOWN, monitor these signals to shift from provisional exploration to committed modeling:

- Ownership, precise meaning, invariants, lifecycle, and integration mechanics have all been explicitly documented and agreed upon by the owning team and domain experts **within one bounded context**.
- A Context Map exists showing the relationship to every other context that references the concept.
- At least one invariant can be proven to be locally enforced by an Aggregate Root with no external dependencies.
  Commit to the model (and reject changes that would dilute it) **only** when all three signals are present. [USER-GROUNDED + derived]

### Anti-Patterns

- **Universal Model Fallacy** (primary): Mistaking a ubiquitous language for an enterprise-wide universal language → semantic coupling, shared muddled models, oversized aggregates, DDD theater. [USER-GROUNDED]
- Big Ball of Mud via shared kernel without explicit boundaries.
- Treating every entity as an Aggregate Root or creating massive aggregates that span contexts.
- "DDD theater": Applying tactical patterns (entities/value objects) without first doing strategic design (bounded contexts + context mapping).
- Allowing synchronous cross-context calls that bypass translation layers. [GROUNDED]

### Uncertainty Handling

- When vocabulary appears shared but ownership is unclear → default to Separate Ways or Anticorruption Layer until proven otherwise; never default to shared model.
- When policy document references a concept used elsewhere → immediately draw (or update) the Context Map and require explicit translation before proceeding.
- Hold all modeling decisions provisional until the three commitment signals above are satisfied.

### Examples of Judgment

**Example 1 (Engineering Policy Review)**  
Situation: New policy document uses "Order" term across Billing, Fulfillment, and Customer Service teams.  
Expert action: Immediately flags shared vocabulary as suspicious. Creates Context Map. Discovers three different invariants. Recommends three bounded contexts + Published Language for the shared ID + Anticorruption Layers for translation. Rejects single shared "Order" model. (Weights local invariants over reuse.)

**Example 2 (Architecture Decision)**  
Situation: Team proposes large shared graph with synchronous calls between services.  
Expert action: Identifies missing context boundaries. Decomposes into smaller aggregates with domain events. Rejects design because it violates semantic isolation. (Signal weighting: invariant protection > synchronous convenience.)

### Grounding Notes

All core reasoning blocks are anchored to STRONG TYPE-R sources (Evans, Vernon, Fowler) and [USER-GROUNDED] expertise description. Two minor policy-application examples remain partially inferred; supply internal engineering policy examples or additional context docs for full refinement in next iteration.
