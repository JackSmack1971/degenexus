---
name: clean-code-structural-refinement
description: Trigger when reviewing, refactoring, or authoring any code change: enforce expert clean-code governance focused on Total Cost of Ownership Delta, Cognitive Load Propagation, actor-based Single Responsibility Principle, and Evolutionary Vector analysis. Activates for maintainability, readability, and structural refinement decisions in software engineering.
---

# Activation

Activate this skill on **any code touch** (new feature, bug fix, refactor, or review). Trigger keywords: "refactor", "review this code", "improve readability", "reduce technical debt", "clean up", "structure", "maintainability", "cognitive load", "single responsibility", "TCO", "Boy Scout Rule".  
Do **not** activate for pure execution/debugging without a human-reader lens.

# Expert Salience

**Load-bearing situational features** (ignore everything else until these are addressed):

- **Future TCO Delta** — Does this change reduce (or at least not increase) long-term ownership cost for the *next* human reader?
- **Local Reasoning** — Can a reader understand this code with *minimal* jumping across files or transitive navigation?
- **One Reason to Change** — Does this module/function have exactly one clear actor/invariant/direction of change?
- **Cognitive Load Propagation** — Are we forcing the reader to hold external context, mixed abstractions, or hidden side effects?
- **Abstraction Stability & Blast Radius** — Are volatile dependencies isolated? Will this change stay localized?

These five signals dominate; superficial metrics (passes tests, looks pretty) are noise unless the above are satisfied.

# Mental Models

- **Total Cost of Ownership Delta** — Code is written for humans first. Every change must leave the codebase cheaper to own tomorrow than today. Intermediate practitioners optimize for "it works now"; experts optimize for "the next reader understands instantly."
- **Cognitive Load Propagation** — Complexity spreads like heat. Transitive navigation, mixed abstraction levels, artificial coupling, and hidden side effects force readers to hold too much context, propagating load system-wide.
- **Actor-based Single Responsibility Principle** — A unit of code has semantic identity only when it shares *one clear reason to change* with the same actor, invariant, and direction of change. Structural similarity is not identity.
- **Evolutionary Vector Analysis** — Treat the codebase as a dynamic system of decoupled change paths. Map vectors by "likely changes remain local." Minimize blast radius through locality; prioritize abstraction stability over local cleanliness.

# Thinking Rules

- Write code primarily for the next human reader, not the compiler.
- Never preserve bad structure just because it already exists.
- Reduce technical debt; never merely relocate it.
- Comments must never compensate for bad naming or structure — fix the code first.
- Names must reveal intent; one word per concept across the codebase.
- Prefer the simplest design that passes all relevant tests.
- Keep related concepts close together; separate constructing a system from using it.

# Decision Heuristics

- If a change forces transitive navigation or mixed abstractions → inline or split immediately.
- If two blocks share "one clear reason to change" → deduplicate unless merging creates artificial coupling.
- If modularity destroys local reasoning → inline the abstraction; it no longer earns its cost.
- If a dependency is third-party or volatile → isolate behind a narrow local adapter.
- When editing: always apply Boy Scout Rule — leave the touched code cleaner than you found it.

# Commitment Thresholds

Commit to refactoring (irreversible action) when **any** of the following load-bearing signals are present:  

- Boolean control flags, long parameter lists, hidden side effects, or mixed abstraction levels.  
- Vague/misleading names or duplicated logic.  
- Artificial coupling between unrelated concepts or hidden logical dependencies.  

**Non-negotiable rule**: Do not leave touched code less readable than before.  
If these signals are absent and the change improves (or at least preserves) local reasoning + TCO Delta, *then* commit.  
(When threshold is unknown: monitor for the above smells during every diff review; they move you from provisional assessment to committed action.)

# Anti-Patterns

- Functional sufficiency bias — accepting code because "it works now" while ignoring compound-interest technical debt.
- Using comments to explain confusing logic instead of fixing names/structure.
- Creating misleading abstractions or unnecessary indirection that destroy local reasoning.
- Mixing data containers and business behavior arbitrarily.
- Treating structural similarity as semantic identity without confirming same actor/invariant/direction of change.
- Grand redesigns when incremental refinement (emergent design) would suffice.
- Leaving touched code less readable than you found it.

# Uncertainty Handling

- Ground abstractions in *known local needs*, never guesses about future implementations.
- Split behavior into separate functions instead of boolean flags; eliminate hidden side effects so the name is truth.
- Use tests as epistemic probes — add learning tests or focused integration tests for unknowns.
- Treat flaky/skipped/ignored tests or spurious failures as unresolved questions (possible concurrency defects until proven otherwise).
- When in doubt, apply the simplicity rule: prefer the simplest design that passes all relevant tests.

# Examples of Judgment

**Scenario 1 (TCO Delta)**: A feature works but introduces a boolean flag and comment explaining the logic.  
Expert judgment: Reject. The flag signals mixed responsibilities; the comment signals poor naming. Refactor to two separate functions with intent-revealing names. TCO decreases even though "it already worked."

**Scenario 2 (Cognitive Load + SRP)**: Two similar-looking validation blocks in different modules.  
Expert judgment: Apply "Reason to Change" test. If same actor/requirement would change both, deduplicate. If merging creates artificial coupling → keep separate. Local reasoning test decides final weighting.

**Scenario 3 (Evolutionary Vector)**: Adding a new external API call directly into business logic.  
Expert judgment: Blast radius too large. Immediately extract narrow adapter. This isolates volatility, keeps change paths decoupled, and protects abstraction stability. Even if locally "cleaner" to inline, systemic evolvability demands the boundary.

**Scenario 4 (Uncertainty)**: Ambiguous legacy code with hidden side effects.  
Expert judgment: Do not guess. Add focused integration tests to map behavior, then split into explicit functions. Provisional until tests confirm; commit only after readability improves.

# Grounding Notes

100% [USER-GROUNDED] from provided expert prose + Skill Wizard authoring standard. All sections anchored in direct TYPE-R rationale on salience, mental models, heuristics, and thresholds. No inference. Ready for validation with `skills-ref` or `skills-validator`.
