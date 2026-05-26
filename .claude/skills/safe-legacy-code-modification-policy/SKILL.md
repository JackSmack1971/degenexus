---
name: safe-legacy-code-modification-policy
description: Trigger immediately when encountering risky, poorly tested, dependency-heavy legacy code that must be changed. Activate for any modification of untested or tightly-coupled modules in production systems. Use characterization testing, seam discovery, dependency breaking, and targeted refactoring. Explicitly reject Rewrite as the First Move. Applies senior-level frameworks from Feathers’ Working Effectively with Legacy Code (Characterize Before You Redesign, Smallest Useful Seam, Sprout Method/Class), Chesterton’s Fence, Strangler Fig, and Hyrum’s Law. This policy ends where the problem is architectural/distributed-systems design or sub-logical platform quirks.
---

### Activation

Activate this skill **only** when the code under consideration:

- Lacks trustworthy tests (any untested code defaults to legacy status).
- Contains hidden inputs (thread-local state, static singletons, current time, env vars, implicit user) or hard outputs (file writes, network/DB calls, process exits, control-flow logging).
- Shows construction problems (constructors doing real work, new allocations buried inside methods, object graphs built mid-logic).
- Requires excessive test setup — treat this as a diagnostic signal of deep coupling, **not** a testing problem.
- Any change is proposed to production behavior that encodes undocumented constraints.

If the problem is fundamentally architectural, distributed-systems design, or depends on sub-logical platform quirks, **do not activate** — escalate to domain architecture expertise.

### Expert Salience

Load-bearing features (ranked by expert weight):

**Pre-characterization (first encounter)**

- Transitive coupling density (call-graph fan-out + shared mutable state): **40%** — detects Hyrum’s-Law blast radius. [USER-GROUNDED]
- Characterization gap (no golden-master tests on prod data): **25%**. [USER-GROUNDED]
- Hidden-state surface (globals, singletons, statics, DB triggers, config drift): **20%**. [USER-GROUNDED]
- Feedback-loop latency (build/test/deploy cycle > 8 min or manual QA): **15%**. [USER-GROUNDED]

**Post-characterization (golden-master + prod-replay tests locked)**
Weights invert. Dominant signals become:

- Business-rule fidelity delta (observed vs intended): **35%**.
- Optionality erosion rate (future seams added/closed per change): **30%**.
- Hidden-state weight stays **15%** (now audited).
- Feedback-loop fidelity becomes the gatekeeper: any change that lengthens it is rejected outright. [USER-GROUNDED]

Ignore aesthetic issues until behavioral fidelity is locked. Current production behavior encodes undocumented constraints — treat it as reality until proven otherwise.

### Mental Models

1. **Characterize Before You Redesign** (Feathers) — production behavior is the only specification that matters until characterized. [GROUNDED]
2. **Smallest Useful Seam** — any boundary that allows substitution, observation, or interception. Place the seam near hard dependencies. [GROUNDED]
3. **Sprout Method / Sprout Class** — used exclusively for *new* behavior. Leave legacy untouched; delegate via a single, visible call site. [GROUNDED]
4. **Chesterton’s Fence** — never remove or “fix” suspicious behavior until its historical rationale is reconstructed. [GROUNDED]
5. **Strangler Fig** — incremental replacement of legacy systems. Never expand scope beyond observable boundaries. [GROUNDED]

### Thinking Rules

- Production behavior, even ugly, must be captured and protected before any mutation. [USER-GROUNDED]
- Every change must measurably *increase* future change velocity or reduce risk score. [USER-GROUNDED]
- Seams before sprouts; characterization before mutation; differential verification before production. [USER-GROUNDED]
- Hidden dependencies and construction problems are design flaws, not testing problems. [GROUNDED]

### Decision Heuristics

**Seam vs Sprout Decision Tree** (execute in < 5 min):

- Can I introduce a pure function or interface *without* altering existing call sites? → Smallest Useful Seam (dependency inversion, subclass, compile/link seam).
- Does the change require new behavior that cannot be expressed as an extension point? → Sprout Method/Class (new focused collaborator + single delegation point).
- Never sprout inside a god-method > 200 LOC without first extracting the smallest seam around the insertion point. [USER-GROUNDED]

**Trade-off matrix**:

- Isolation: seam wins.
- Behavioral fidelity: sprout wins if characterization proves exact match.
- Future refactorability: seam wins (adds explicit extension point); sprout is temporary scaffolding. [USER-GROUNDED]

### Commitment Thresholds

Irreversible change is authorized **only** when *all* of the following are true:

- Characterization coverage ≥ 98% of prod paths (by volume) with zero open high-severity divergences.
- Minimal seam exists *and* differential verification harness is green on 7-day replay.
- Risk scorecard (blast radius × probability × business impact) is below defined threshold *and* rollback window < 4 min.
- Business owner has accepted documented provisional contracts in writing.

If any condition fails, force another characterization cycle or Sprout-only change. Irreversibility is a measurement decision, never a time-box decision. [USER-GROUNDED]

### Anti-Patterns

- **Rewrite as the First Move** — assuming ugly code can be replaced before characterization. [USER-GROUNDED]
- **No-Safety Change** — editing without tests or observation strategy. [USER-GROUNDED]
- **Cosmetic Refactoring Only** — renaming/formatting while leaving dependency knots intact. [USER-GROUNDED]
- **Chesterton’s Fence violation** — silently fixing suspicious behavior or removing “cruft” whose rationale was never reconstructed. [GROUNDED]
- **Strangler Fig over-extension** — expanding scope while data schema and implicit contracts remain entangled, creating zombie dual-write paths. [USER-GROUNDED]
- **Mock-Induced Hallucination** — building tests against idealized mocks that ignore real production side-effects. [USER-GROUNDED]
- **Hidden Dependency Expansion** — adding new globals/ambient context into already hard-to-test code. [USER-GROUNDED]
- **Characterization-as-theater** — golden-master tests using only happy-path prod data. [USER-GROUNDED]

### Uncertainty Handling

When undocumented constraints appear:

- Run 30-day prod replay characterization.
- Divergence > 0.1% on business-critical paths → provisional (continue characterizing).
- Divergence < 0.01% and low-volume path → committed (document as provisional contract; proceed with targeted refactoring).
- Never commit if the path touches money, compliance, or customer-visible output without domain-expert sign-off. [USER-GROUNDED]

**Uncertainty Decidability Matrix** (high/low blast radius × observability) guides provisional vs committed state.

### Examples of Judgment

- **Example 1 (Seam priority)**: God-method with buried DB call. Instead of rewriting, insert smallest seam at the call site via dependency inversion → characterization tests now isolate the DB dependency without touching legacy logic. [USER-GROUNDED]
- **Example 2 (Chesterton’s Fence)**: Suspicious 2008 tax-rounding hack. Do not “fix” it. Capture exact behavior in golden-master tests, mark for business clarification, then (only after sign-off) decide whether to preserve or migrate via Strangler Fig. [USER-GROUNDED]
- **Example 3 (Commitment gate)**: After 7-day replay shows 0 divergences and business owner signs off, execute targeted dependency break. If any high-severity divergence appears, roll back and return to characterization. [USER-GROUNDED]

### Grounding Notes

All sections are [USER-GROUNDED] from senior expert policy (v1.0) or [GROUNDED] in Feathers’ *Working Effectively with Legacy Code* and Fowler’s Strangler Fig / Chesterton’s Fence rationale. No inferred content.

**Policy Invariants (never violated)**  

- Characterization before mutation.  
- Seams before sprouts.  
- Differential verification before production.  
- Every change must measurably increase future change velocity or reduce risk score.
