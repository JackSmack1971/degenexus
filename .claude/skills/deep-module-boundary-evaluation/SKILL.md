---
name: deep-module-boundary-evaluation
description: Triggers on any module-boundary proposal, refactor, or legacy audit in software architecture. Use when deciding whether a boundary qualifies as deep (hides volatility behind simple interface, contains cognitive load) versus shallow ceremony (leaks secrets, amplifies change). Cultivates principal-level expert salience: weighting depth ratio, volatility containment, propagation index, and future change vectors. Never commit on intuition—simulate vectors first.
---

# Activation

Activate this skill whenever you are:

- Evaluating a proposed module, interface, or facade boundary.
- Refactoring legacy code that exhibits information leakage or tactical decomposition.
- Conducting architecture decision records (ADRs), PR reviews, or quarterly boundary re-evaluations.
- Simulating future change vectors to forecast cognitive-load spread.

If the task is purely procedural implementation inside an already-committed deep boundary, do not activate.

# Expert Salience

Load-bearing features (ranked by weight):

- **Depth ratio** (primary, ≥4:1 target): (internal conceptual/LOC complexity hidden) ÷ (public surface: method count + param/return types + exceptions). [USER-GROUNDED][GROUNDED]
- **Volatility containment score** (tied primary, 40% higher weight): Every design decision ranked by historical commit frequency + business/tech risk; must achieve 100% encapsulation—no client-visible leakage of secrets (DB schemas, error taxonomies, auth flows, etc.). [USER-GROUNDED][GROUNDED]
- **Propagation index** (secondary): Average number of client modules/tests touched by a simulated change. Threshold ≤1.5. [USER-GROUNDED][GROUNDED]
- **Cognitive surface audit** (tie-breaker): Can a new developer understand the public contract in <5 minutes without reading implementation? Interface bloat >10% of module size = reject. [USER-GROUNDED][GROUNDED]

Ignore raw LOC or “clean-looking” interfaces. Shallow ceremony is any boundary where SAVR (Surface-Area-to-Volume Ratio) ≥1.0, SVC (Secret Volatility Coefficient) approaches 1.0, or Choreography Index >3 (caller forced into multi-step sequencing). [GROUNDED]

# Mental Models

- **Deep Modules** (Ousterhout): A module is deep when a small, simple public interface hides massive internal complexity. Cognitive load stays inside the boundary. [GROUNDED]
- **Information Hiding** (Parnas): Hide design decisions that are likely to change behind stable interfaces. Clients depend only on the interface, never on secrets. [GROUNDED]
- **Pull Complexity Downward**: Move messy logic, state machines, third-party quirks, and edge-case orchestration into the module so callers remain simple. Change amplification is the enemy. [GROUNDED]
- **Change Amplification Analysis**: Simulate future vectors and ask: “Where does cognitive load spread?” If it spreads beyond the module, the boundary is shallow.

# Thinking Rules

- A boundary is justified *only* when it hides meaningful volatility or policy behind a simpler interface. Otherwise it is shallow ceremony that merely relocates complexity. [GROUNDED]
- Information leakage (any exposure of hidden types, sequencing, invariants, or implementation details) is the cardinal sin. [GROUNDED]
- Tactical programming (flags, wrappers, layers, pass-throughs) that makes code look cleaner while leaking secrets must be corrected on sight. [USER-GROUNDED]
- Always prefer one deep module encapsulating one secret over many shallow modules. [USER-GROUNDED]

# Decision Heuristics

- If depth ratio <2:1 or volatility containment <100% → treat as shallow ceremony; reject or deepen. [USER-GROUNDED]
- If propagation index >1.5 on any simulated vector → boundary fails; pull complexity further down or collapse. [USER-GROUNDED]
- If Choreography Index >3 → collapse sequencing inside the module (single command method). [USER-GROUNDED]
- When adding a new feature that touches leaked secrets across multiple sites → extract into a new deep module rather than patching callers. [USER-GROUNDED]

# Commitment Thresholds

Move from provisional analysis to irreversible refactor/commitment *only* when **all three** gates pass:

1. ≥2 change vectors have been simulated with average propagation ≤1.5.  
2. Depth ratio ≥4:1 *and* volatility containment = 100%.  
3. Facade integrity check passes (static analysis shows no external imports of hidden types; historical coupling audit clean).  

Stay provisional otherwise—use strangler facade, feature flag, or inline duplication. Business pressure overrides only if projected 3× maintenance cost is exceeded *and* documented in risk register. Never commit on “feels deep.” [USER-GROUNDED]  
Quarterly re-eval on all committed boundaries.

# Anti-Patterns

- **Premature deep abstraction (YAGNI bloat)**: High depth ratio but zero simulated vectors. [USER-GROUNDED]
- **Boundary inflation / shallow ceremony everywhere**: Propagation index >3 on any change. [USER-GROUNDED]
- **God-module avoidance (fragmentation)**: Dozens of thin modules without hierarchy → rising integration test failures. [USER-GROUNDED]
- **Forecasting bias**: Optimistic stakeholder vectors without historical change-log evidence. [USER-GROUNDED]
- **Tactical decomposition**: Adding flags/wrappers/pass-throughs that leak sequencing or invariants. [USER-GROUNDED]
- **Data-holder / processor split**: Anemic models + external managers that leak invariants. [USER-GROUNDED]

# Uncertainty Handling

In legacy codebases:

- Weight signals via historical commit frequency × afferent coupling (SonarQube/dependency graphs). [USER-GROUNDED]
- Leakage score = % of public members exposing secrets. [USER-GROUNDED]
- Start extraction at *highest-volatility secret only*. [USER-GROUNDED]
- Apply strangler facade + incremental carve-out; test facade integrity after every PR. [USER-GROUNDED]
- If too tangled, accept temporary shallow wrapper *but tag as provisional* and schedule quarterly re-audit. [USER-GROUNDED]
- Use data-flow gravitation over control-flow structure. Never trust “it works”—audit for re-exposure. [USER-GROUNDED]

# Examples of Judgment

**Fintech OrderProcessor (2024)**: Proposed 7 thin adapters. Simulated crypto/PSD2/VAT vectors → propagation = 9 call-sites + 14 tests. Collapsed into deep `FulfillmentEngine` (single `process(Order): Result`). Propagation = 2 internal files. Committed because load stayed contained. [USER-GROUNDED]

**Legacy CRM DataAccessLayer**: 12 call-sites leaking SQL + connection details. Simulated Postgres→Snowflake. Deep facade achieved 5:1 depth ratio and 0 client changes. Committed after integrity check. [USER-GROUNDED]

**Order Execution Router**: Multi-step orchestration exposed temporal coupling. Simulated dark-pool shift. Collapsed to single `executeIntent(ExecutionIntent): Stream<ExecutionEvent>`. Zero orchestration changes on later async introduction. [USER-GROUNDED]

**Local Agentic RAG**: Exposed index topology via config objects. Simulated HNSW transition → would break callers. Deepened to `retrieveRelevantContext(UserPrompt): SemanticPayload`. All topology logic internalized. [USER-GROUNDED]

# Grounding Notes

All salience, heuristics, thresholds, and examples are [USER-GROUNDED] from principal-level expert input. Mental models, thinking rules, and anti-patterns are [GROUNDED] in Ousterhout *A Philosophy of Software Design* (Ch4-6) and Parnas 1972 Information Hiding. No inference used. Validate with `skills-ref` before deployment.
