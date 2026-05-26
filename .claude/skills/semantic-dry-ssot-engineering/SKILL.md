---
name: semantic-dry-ssot-engineering
description: Triggers on any AI-assisted code generation, pull-request review, architecture decision, or refactor involving duplication, automation, or cross-artifact synchronization. Activates to enforce Semantic DRY, Single Source of Truth derivation, Change Propagation Simulation, Automation Leverage Scoring, and Code-as-Liability reasoning so that generated artifacts preserve coherent domain knowledge over time instead of silently accumulating synchronization debt.
---

# Semantic DRY & SSOT Engineering

## Activation

Activate this skill whenever an AI generator (or human) produces code, schemas, prompts, tests, or configuration that could embed the same business rule, invariant, policy, or data mapping in more than one place, or whenever a proposed change would require updating disconnected artifacts. Also activate on any velocity-focused generation run that risks the volume-velocity fallacy.

## Expert Salience

**Load-bearing features** (in descending order of weight):  

1. Knowledge multiplicity (how many artifacts encode the *same* invariant).  
2. Propagation blast radius Φ (number of files/prompts/configs touched by one upstream change).  
3. Determinism index D (0–1) of verification (static types/compiler vs. stochastic/LLM).  
4. Volatility enum of the rule (high = policy/auth/flow changes >2×/year).  
5. Abstraction level (0–1) of the authoritative representation.  

Ignore syntactic DRY (identical text) and surface cleanliness; focus exclusively on whether domain knowledge has a single authoritative node.

[USER-GROUNDED]

## Mental Models

- **Invariant Source Density Model**: Code volume is irrelevant; what matters is the ratio of unique business invariants to the number of distinct system interfaces where those invariants are expressed. Low density = knowledge has leaked.  
- **Information Projection Topology**: Treat the SSOT as a root node that *projects* all downstream representations via deterministic compilation, reflection, or macro-expansion. AI must never author static downstream code; it must author the projector.  
- **Orthogonality Lens** (for CPS): Keep components independent so a single change never forces unrelated changes elsewhere.  

[USER-GROUNDED]

## Thinking Rules

- Every business rule, invariant, policy, or constraint must have *exactly one* authoritative representation.  
- Generated code is acceptable only when it is a deterministic projection of that SSOT.  
- AI generators are tools for eliminating mechanical duplication, never for creating new authoritative knowledge.  
- Synchronization debt is the primary liability; every disconnected artifact multiplies future maintenance cost.  

[USER-GROUNDED]

## Decision Heuristics

- If multiplicity ≥ 2 for any critical rule → force SSOT + generator pipeline (never accept scattered implementations).  
- If propagation_score = N × volatility × (1 − abstraction) > 3 → reject or refactor immediately.  
- If D < 0.8 (stochastic verification) → isolate behind strict SDK/facade before acceptance.  
- If Φ > 1 across structural paradigms → reclassify the automation as a Synchronization Debt Vector and reject.  

[USER-GROUNDED]

## Commitment Thresholds

An artifact remains provisional until it clears *all* of the following gates (tracer-bullet style):  

1. **Verification Determinism Gate**: D ≥ 0.8 (static, compiler-enforced, or mathematically provable).  
2. **Codebase Delta Flux**: Net structural complexity ΔK ≤ 0 after the change.  
3. **Encapsulated Blast Radius**: Φ = 1 (or 0 for fully self-contained modules).  

Commit to core architecture or refactor *only* once a thin end-to-end slice has proven the path *and* the above gates are satisfied. Otherwise maintain informed hesitation and demand the missing signal (missing information or feedback).  

[USER-GROUNDED] — derived directly from the expert’s explicit if/when rules.

## Anti-Patterns

- **Rule Scattering** — identical logic duplicated across UI, API, service, DB, tests, and prompts with no traceable SSOT.  
- **Ghost Coupling** — modules that work together only because of ambient prompt context (invisible to compilers/linters).  
- **Polyglot Invariant Drift** — same rule expressed in PL/pgSQL, Go, TypeScript, etc., creating O(N) verification surface.  
- **Seductive Shimming** — adding adapters/proxies instead of fixing the underlying interface mismatch.  
- **Volume-Velocity Fallacy** — mistaking cheap AI generation for cheap maintenance while multiplying semantic duplication.  
- **Cargo-Cult Process** — rituals, checklists, or docs used as substitute for deterministic automation.  

[USER-GROUNDED]

## Uncertainty Handling

Under missing data or conflicting signals, default conservatively: assume 30 % future change probability, raise abstraction level, and shorten feedback loops. Never accept partial credit — commit only when *all* gates pass; otherwise reject-to-regenerate or isolate. Trace every rule’s provenance explicitly before weighting velocity.  

[USER-GROUNDED]

## Examples of Judgment

**Ex 1 — Email Validation (immediate functionality vs. long-term adaptability)**  
AI generates frontend + backend validation that works now. Signals: immediate OK (weight 0.2) vs. adaptability cost of future policy shift (weight 0.8, N=5 locations, high volatility). Expert commits to JSON Schema SSOT + generator pipeline despite short-term overhead.  

**Ex 2 — High-frequency derivative execution pipeline**  
AI produces optimized raw WebSocket buffer mapping that shaves 12 μs latency but hard-codes exchange layout. Exchange API migration announced in 60 days. Expert rejects static code (D → 0 under stress) and forces compile-time meta-parser driven by JSON schema SSOT. Result: same performance, one-line schema update, D = 1.0.  

**Ex 3 — Enterprise agentic swarm**  
AI generates 40 specialized Python classes for AI workers (high velocity, all tests pass). Expert recognizes 40× verification surface and Volume-Velocity Fallacy. Deletes the classes, replaces with single deterministic state-machine driver + declarative config table. Synchronization debt eliminated.  

[USER-GROUNDED]

## Grounding Notes

All cognitive blocks (salience, models, rules, heuristics, thresholds, anti-patterns, examples) are directly [USER-GROUNDED] from the expert’s answers to the five clarifying questions plus the original expertise description. No inference used. Structural frontmatter and progressive-disclosure mechanics [GROUNDED] in the Skill Wizard authoring specification.
