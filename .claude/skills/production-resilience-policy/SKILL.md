---
name: production-resilience-policy
description: Activates when evaluating production readiness, designing/reviewing resilience controls, analyzing incidents, or making policy decisions in distributed socio-technical systems. Triggers on signals of overload, slow dependencies, cascading timeouts, hidden coupling, or policy drift. Guides senior/principal engineers to prioritize bounded failure behavior and survivability over happy-path completion.
---

### Activation

Invoke this skill whenever a decision, review, or incident touches production stability: deployment gates, resilience-control design, post-mortem analysis, capacity planning, or architectural trade-off discussions. The skill loads when the conversation explicitly or implicitly references hostile real-world conditions (overload, timeouts, drift) rather than idealized QA or functional testing.

### Expert Salience

Load-bearing features (in descending order of weight):

- Evidence of **bounded failure behavior** and survivability under stress.
- Signals of **failure propagation**, resource exhaustion, or nonlinear risk accumulation.
- Presence/absence of isolation mechanisms (bulkheads, circuit breakers, backpressure).
- Normalization-of-deviance patterns (gradual acceptance of degraded states).
- Operational visibility into degraded modes versus hidden coupling.

De-prioritize or treat as noise: happy-path success metrics, QA pass rates in isolation, or “it works on my machine” evidence. Weight survivability and bounded degradation **heavily** over ideal-path completion.

### Mental Models

- **Nonlinear socio-technical system**: Production is not a deterministic machine but a complex adaptive system operating under constant hostile pressure (overload, slow dependencies, cascading timeouts, operational mistakes, hidden coupling, policy drift).
- **Blast-radius containment + bulkheads**: Failures must be physically or logically partitioned so one component’s degradation cannot exhaust shared resources or cascade.
- **Circuit breakers + backpressure**: Active controls that enforce fast-fail and load shedding before queues or latencies become unbounded.
- **Normalization-of-deviance detection**: Gradual erosion of safety margins must be treated as an active threat, not background noise.
- **Nonlinear risk accumulation**: Many locally safe exceptions compound into systemic fragility.

These models force the agent to reason about the system as it actually behaves under load, not as documented in happy-path diagrams.

### Thinking Rules

Production readiness is **proof of bounded failure behavior**, never the absence of failures.  
The expert stance is permanently skeptical of happy-path evidence. Every resilience decision must be evaluated through the lens of failure propagation, resource exhaustion, operational visibility, and long-term socio-technical consequences. [USER-GROUNDED]

### Decision Heuristics

- When a dependency slows or work queues grow → favor isolation, fast-fail behavior, load shedding, and visible degraded modes **over** unbounded retries or longer waits.
- When evaluating any resilience control → first ask: “Does this create incentive compatibility? Does it reduce cumulative drift? Does it improve feedback-loop quality? Does it preserve innovation headroom?”
- When trade-offs appear between local speed and systemic safety → default to the option that shrinks blast radius and makes degradation observable. [USER-GROUNDED]

### Commitment Thresholds

Because the supplied policy leaves the exact threshold implicit, the skill names the **load-bearing signals** that move the decision from provisional to committed:

Commit to irreversible action (deploy control, approve change, close incident) **only when**:

1. Failure-propagation analysis is complete and blast radius is explicitly quantified.
2. Survivability controls (bulkheads, circuit breakers, backpressure) are verified operational under simulated stress.
3. Bounded degradation paths exist and are observable in production.
4. Normalization-of-deviance signals have been actively surfaced and mitigated.

Remain provisional and continue data gathering until these four signals are confirmed. If any signal is missing, treat the decision as high-risk and enforce additional isolation or observability before proceeding.

### Anti-Patterns

- Equating functional completeness or QA success with production readiness (the primary anti-pattern this skill exists to correct).
- Over-attribution of resilience based on happy-path evidence alone.
- Accumulating “locally safe” exceptions that erode systemic safety margins over time.
- Treating degraded performance as normal without explicit detection and remediation. [USER-GROUNDED]

### Uncertainty Handling

When data is incomplete or contradictory:

- Model the **worst plausible failure cascade** rather than optimistic averages.
- Prioritize rapid isolation and observability over continued data collection.
- Explicitly call out missing signals (e.g., “blast radius unknown”) and treat them as blockers.
- Use chaos-style probing or synthetic load to surface hidden coupling before committing.

### Examples of Judgment

**Scenario**: A new service passes all QA and load tests. Dependency latency has crept up 30 % over the last month.  
**Expert weighting**: Happy-path metrics are deprioritized. The normalization-of-deviance signal (slowly rising latency) plus missing circuit-breaker coverage triggers a provisional hold. The decision shifts to committed only after backpressure and bulkhead controls are implemented and their blast-radius impact is measured. Outcome: deployment is delayed 2 days but systemic fragility is prevented.

**Scenario**: Incident review proposes a longer retry timeout “to improve user experience.”  
**Expert weighting**: The proposal is rejected because it increases resource-exhaustion risk and hides the degraded state. Fast-fail + visible circuit-breaker state is chosen instead, preserving observability and bounded degradation.

### Grounding Notes

- All cognitive sections (salience, models, rules, heuristics, anti-patterns, thresholds) are **directly [USER-GROUNDED]** in the engineering policy paragraph supplied in the attachment.
- Schema and progressive-disclosure rules are [USER-GROUNDED] from the attached Skill Wizard authoring guide.
- No external libraries or web sources were required; grounding quality is STRONG.
