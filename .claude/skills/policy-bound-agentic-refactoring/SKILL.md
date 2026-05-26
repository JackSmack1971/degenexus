---
name: policy-bound-agentic-refactoring
description: Activated on any AI-generated refactor proposal, smell detection, structural improvement attempt, or edit diff in a codebase governed by binding operational engineering policy. Triggers the Diagnose → Treat → Verify → Stop loop, enforces Semantic Conservatism, treats every agent diff as a falsifiable hypothesis, and gates all commits behind policy fidelity, runtime invariants, and ownership boundaries.
---

### Activation

Trigger this skill **immediately** whenever:

- An AI agent (or any automated tool) proposes a code change, refactor, smell remediation, or structural edit.
- Static analysis surfaces a smell (bloaters, object-orientation abusers, change preventers, dispensables, couplers, or library gaps).
- A human requests “cleanup,” “refactor,” or “improve structure” on any module.

If the proposal does not originate from an AI agent or does not touch code under binding operational policy, remain dormant.

### Expert Salience

Load-bearing situational features (in strict descending order of weight):

- **Policy invariants & fidelity delta** — absolute gate (∞ weight). Any silent behavior change = rejection.
- **Runtime behavior preservation** (shadow execution + differential fuzzing under production-like loads) — next hard gate.
- **Ownership boundaries, coupling metrics, and public API surface** — halt if crossed without explicit approval.
- **Static smell scores** (Cyclomatic Complexity, duplication, etc.) — lowest weight (≈0.1); acted on *only* if all higher signals are neutral or positive.

Static smells alone never trigger commitment. Compute composite score; reject if *any* hard invariant is violated or net fidelity delta > 0.01.

### Mental Models

- **Diagnose → Treat → Verify → Stop** [USER-GROUNDED]: Core executable loop. Diagnose names the exact smell + maintenance cost and confirms it is structural (not style). Treat selects the *smallest* catalog technique and states the expected cleaner end-state *before* editing. Verify runs existing tests/characterization checks after every risky step. Stop exactly when the named smell is materially reduced, the next improvement requires re-diagnosis, or further work becomes speculative.
- **Semantic Conservatism** [USER-GROUNDED]: Zero observable semantic surface change unless the proposal carries an explicit, policy-approved requirement. Legacy code contains undocumented load-bearing side effects; treat every block as a state-mutation matrix.
- **Treatment-as-Hypothesis** [USER-GROUNDED]: Every AI-generated diff is a falsifiable clinical hypothesis, never “the agent’s intent.” Log agent self-explanation *and* independent harness output; the two must converge before advancing.
- **Smell Priority Hierarchy** [USER-GROUNDED]: Scan in fixed order: bloaters → object-orientation abusers → change preventers → dispensables → couplers → library gaps.

### Thinking Rules

- Every AI diff is a hypothesis to be aggressively falsified, not trusted. [USER-GROUNDED]
- Policy fidelity and invariant integrity are non-negotiable hard gates. [USER-GROUNDED]
- Prefer local simplifications and renames over broader hierarchy changes. [USER-GROUNDED]
- A simple, honest conditional or intentional extension point beats mechanical application of modern patterns if the abstraction obscures a direct business rule. [USER-GROUNDED]
- Scope is strictly bounded: new smells discovered during an edit are recorded separately unless they actively block the current change. [USER-GROUNDED]

### Decision Heuristics

- IF a proposed treatment alters existing behavior silently → reject immediately.
- IF a change threatens to cross code ownership boundaries, alter public-facing APIs, or expand beyond approved feature scope → halt and escalate.
- IF duplication is merely coincidental (likely to diverge for different business reasons) → do not merge into shared abstraction.
- IF variation is not yet stable and genuinely owned by type or state → do not replace simple conditionals with polymorphism.
- IF the next improvement requires a different diagnosis or becomes speculative → STOP.

### Commitment Thresholds

Commit an AI-generated refactoring to a permanent edit **only** when *all* of the following are simultaneously true [USER-GROUNDED]:

- policy_fidelity_delta ≥ 0.99 (embedding similarity or oracle verification).
- 100 % runtime invariants hold in shadow environment (including adversarial inputs).
- Net coupling decrease *and* ownership boundary compliance.
- Expert uncertainty score < 0.15 (composite of provenance gap + trace diff magnitude).
- No conflicting signals between agent explanation and independent harness.

Otherwise the proposal remains in “hypothesis” state; no edit is applied.  
Additional explicit rules derived from the stated commitment threshold:

- Small Steps: apply as a sequence of tiny changes; program must remain working after *each* meaningful step.
- Tests/characterization checks must pass after every risky step; never delete failing tests to make a refactor appear successful.
- Final Stop Condition: halt and commit only when the originally named smell is gone, the code is clean enough for the requested change, or the refactoring crosses boundaries requiring explicit approval.

### Anti-Patterns

- **Teleological Fallacy of Agent Intent** [USER-GROUNDED]: Treating stochastic token completions as purposeful, goal-directed understanding; over-trusting agent self-explanation without cross-checking runtime non-determinism or policy erosion.
- Scope creep / open-ended cleanup pass: continuing to refactor simply because a new smell appears during an edit.
- Substituting coincidental similarity for genuine shared abstraction.
- Idiom cascade: introducing complex modern abstractions (streams, generics, reactive patterns) that satisfy the agent’s internal “clean code” drive but increase cognitive load and hidden overhead.
- Localized regression blindness: local tests pass while non-local invariants break three layers up the call stack.
- Anthropomorphic verification bias: letting the agent’s markdown explanation substitute for rigorous diff + telemetry review.

### Uncertainty Handling

Default stance is **provisional**: log, simulate, annotate, do not commit. [USER-GROUNDED]

- If a chain of small edits is not visibly improving clarity → pause and re-diagnose rather than pushing forward.
- When a smell requires human judgment about intent (algorithm that resists simpler structure, comments on non-obvious external constraints) → collaborate with author or escalate.
- If refactoring exposes a different, larger problem → stop current transformation and report new scope.
- Visible smells intentionally left untreated (worse tradeoffs, external constraints) → explicitly document or report.
- Principle of Empirical Primacy: independent deterministic verification systems (compilers, profilers, shadow execution) possess absolute epistemic authority over natural-language agent assertions.

Escalate to human review on:

- Invariant-level conflicts or policy deadlocks.
- High-impact modules (ownership score above threshold).
- Provenance gaps that cannot be closed by additional harness runs.
- Socio-technical disintegration (architecture mess caused by Conway’s Law / organizational friction — not an AST problem).

### Examples of Judgment

1. **Agent proposes extracting duplicated logic** → Expert runs Treatment-as-Hypothesis: checks whether duplication is coincidental (different business reasons expected to diverge). Finds divergence likely → rejects merge, documents as non-treatment. (Signal weighting: business-rule ownership > static duplication score.)
2. **Agent suggests replacing conditional with polymorphism** → Variation not yet stable → heuristic fires: keep simple conditional. Runs shadow execution → confirms no behavior change → stops after minimal rename. (Stop Condition satisfied.)
3. **During edit, new smell appears** → Teleological Fallacy trap detected → records new smell separately, does not expand scope. Commits only after original smell is resolved and all gates pass.
4. **Agent claims thread-safety** but static analysis flags race → Empirical Primacy: shadow execution under load reveals race → rejects, escalates with trace diff. (Uncertainty handling in action.)

### Grounding Notes

All cognitive content is [USER-GROUNDED] from the expert practitioner’s own mental models, signal-weighting protocol, commitment thresholds, and observed failure modes. Meta-structure follows the Agent Skills standard. No inference used. To strengthen further, supply example refactoring case studies or policy oracle implementation details.
