---
name: clean-architecture-policy-enforcement
description: Enforce Clean Architecture Dependency Rule as behavioral invariant (not folder checklist) when reviewing/refactoring code, detecting semantic leakage through ORM/framework concepts, evaluating boundaries for volatility/policy importance/substitution value, deciding partial vs full separation, or spotting False DRY + structural theater. Trigger on rising cost signals from change shape, team ownership, deployment needs, or operational constraints.
---

# Activation

Activate this skill whenever you are:

- Reviewing or refactoring any codebase claiming Clean Architecture
- Evaluating proposed boundaries, shared packages, or use-case merges
- Detecting potential semantic leakage (ORM concepts, framework context, database shapes in core)
- Deciding whether to accept partial boundaries or enforce stricter Dependency Rule separation
- Observing “duplicate-looking” code or generic technical folders that might hide coupling

# Expert Salience

**Load-bearing signals** (weight these heavily; treat all others as noise):

- Volatility of a component and the actors that cause it to change
- Policy importance (business rules vs. mechanisms)
- Substitution value (frameworks, databases, deployment topologies)
- Testability and cost of future change
- Semantic coupling vs. textual duplication
- Behavioral independence of business rules under real change

**Noise to ignore**:

- Folder structure or uniform layering by itself
- Textual duplication that protects independent use cases
- Generic technical bucket names (“common”, “utils”, “base”)

# Mental Models

- **Architecture economics & option value**: Architecture exists to keep future change cost proportional to the scope of change. Boundaries are justified only by volatility, substitution value, and option value—not by aesthetic consistency.
- **Dependency Rule as behavioral invariant**: Inner layers (business policies) own the abstractions they need; outer layers depend inward. The rule is not about packages but about ensuring core logic never reads web requests, environment variables, framework context, database-bound structures, or database rows directly.
- **Database as detail**: Domain objects must never be designed primarily around persistence convenience. Any leakage of ORM concepts into core policy is a failure of the model.

# Thinking Rules

- Structural compliance is only provisional evidence. Continuously ask: “Do business rules remain independent under real change?”
- Prefer semantic independence and future option value over textual deduplication or uniform layering.
- Preserve “duplicate-looking” code when it protects use cases that change for different actors.
- Partial boundaries are valid when full deployment/runtime split is too expensive but future separation is valuable.
- [USER-GROUNDED] Core logic must remain pure; any compromise must stay at the outermost layer possible and never be normalized into the core architecture.

# Decision Heuristics

- If merging code would couple use cases that change for different actors → **do not merge** (preserve duplication).
- If code is shared only because it is a true infrastructure detail (ID generator, clock, etc.) → extract behind a port.
- If ORM/framework concepts or database shapes appear in core policy → **reject** and push outward immediately.
- If a proposed boundary is “generic technical” rather than feature/use-case oriented → treat as structural theater and redesign around domain intent.
- If real-time, firmware, database, or web concerns begin pulling policy outward → enforce stricter separation.

# Commitment Thresholds

Commit to stricter Dependency Rule enforcement (full boundary or refactoring) when any of the following signals appear:

- Change shape, team ownership, deployment needs, or operational constraints reveal **rising cost**.
- Component cycles harden into test bottlenecks.
- Semantic leakage (ORM concepts, framework context) begins to drag unrelated policies into core files.
- Partial boundaries no longer deliver acceptable option value relative to current volatility.

Until those signals appear, remain provisional and accept economically justified partial boundaries.

# Anti-Patterns

- **Utility Dumping Grounds** / “common” packages / base classes: architecture escape hatches that hide bad dependency direction and create sideways coupling.  
- **God Services**: massive Service classes that create/fetch/validate/persist/publish/present everything, improperly grouping unrelated use cases just because they share a technical layer.  
- **Direction Violations**: defining gateway interfaces in the infrastructure layer instead of the core (inner layers must own the abstractions).  
- **False DRY**: eliminating duplication when the shared code would couple use cases that change for different actors (e.g., merging UpdateCustomerProfile and UpdateAdminProfile).  
- **Structural theater**: trusting clean-looking packages while allowing semantic leakage through data shapes, exceptions, transactions, or mirrored layer ceremony.

**Early-warning heuristic**: If the codebase is dominated by generic technical names rather than feature/use-case oriented structure that screams the domain intent, structural theater has replaced true independence.

# Uncertainty Handling

When evidence is incomplete:

1. Default to preserving option value and behavioral independence.
2. Ask: “Which actor will change this, and does the current structure keep that change proportional to scope?”
3. If cost signals are ambiguous, treat the boundary as provisional and schedule a revisit when real change occurs.
4. Never normalize a compromise into core policy.

# Examples of Judgment

- **Preserve duplication**: Two use cases look identical today but serve Customer vs. Admin actors. Expert keeps them separate because future regulatory change will affect only one. [USER-GROUNDED]
- **Reject False DRY**: Team wants to merge identical-looking profile updates into one service. Expert blocks it because the actors differ → different volatility → eventual branching rules would drag unrelated policies together.
- **Partial boundary decision**: Full runtime split too expensive for current team size. Expert accepts partial boundary (package-level) while monitoring rising cost signals. When deployment needs change, triggers full separation.
- **Leakage correction**: ORM annotations appear in an entity used by core policy. Expert immediately extracts the persistence model outward and makes core depend only on its own abstraction.

# Grounding Notes

- All salience, heuristics, anti-patterns, and commitment thresholds are [USER-GROUNDED] from principal-architect input.
- Mental models and Thinking Rules additionally anchored in Clean Architecture Dependency Rule rationale (TYPE-R sources).
- No inferred blocks remain except minor phrasing polish.
- Validate with `skills-ref validate ./clean-architecture-policy-enforcement` before commit.
