---
name: disciplined-code-refactoring-policy
description: Triggered whenever a developer is considering structural changes to code (refactoring) during feature implementation, bug fixing, code review, or when a change feels awkward due to structure. Activates senior/principal-level judgment for improving internal structure without altering observable behavior, governed by economic reasoning, preparatory refactoring, intent separation, small safe steps, and safety nets.
---

### Activation

Activate this skill on any prompt containing: "refactor", "cleanup", "improve structure", "code smell", "divergent change", "shotgun surgery", "feature envy", "make this change easier", "mixed-intent", "big rewrite", or when evaluating a PR/patch that touches both structure and behavior. Also activate before any structural edit that risks observable behavior or when roadmap timing intersects with technical debt.

### Expert Salience

**Load-bearing signals** (principal-level weighting — ignore aesthetics; focus on friction that blocks the *immediate next change* [USER-GROUNDED]):  

- **Classic smells**: Divergent change (one class changes for many unrelated reasons), shotgun surgery (one functional change forces edits across many files), feature envy (method uses data from another class more than its own).  
- **Structural friction**: Heavy global state, hidden side effects, "too much context to change safely".  
- **Quantitative signals** (fused principal practice): Churn-complexity hotspots (commits/90d × cognitive complexity), spatial coupling index (co-change probability across files), ownership fragmentation (bus factor ≤2 or >40% blame on one dev), production telemetry (P95 latency contribution, error-budget burn, defect density).  
  High signal weight on localized friction + roadmap proximity; low weight on generalized "clean code" without immediate payoff.

### Mental Models

- **Preparatory Refactoring** (Fowler/Beck [GROUNDED]): "Make the change easy, then make the easy change." When a feature request arrives, ask: "What makes this change awkward?" → perform the local structural change that makes the desired feature straightforward.  
- **REARF (Refactoring Economics & Risk Assessment Framework)** [USER-GROUNDED]: 2×2 matrix (Blast Radius vs. Systemic Yield/Value) integrated with roadmap timing. Quadrants dictate action: High-Value/Low-Radius → broad refactor now; High-Value/High-Radius → micro + flag + deferral tied to exact milestone; Low-Value → documented deferral.  
- **Risk-Yield Allocation Matrix** [USER-GROUNDED]: Blast Radius (coupling × telemetry × verification) vs. Systemic Yield (velocity dividend). Roadmap Proximity Vector decays value exponentially if >2 quarters out.  
- **Steady Design Improvement** [USER-GROUNDED]: Structural improvement is daily work, never a separate phase. "Work in Small Steps" — many small safe edits over one large transformation.

### Thinking Rules

- Refactoring must strictly preserve observable behavior; economic reasoning (friction reduction vs. blast-radius cost) always trumps aesthetic preference [USER-GROUNDED].  
- Every proposed cleanup is a hypothesis whose value must be proven against immediate change friction, not future speculation.  
- "Steady design improvement as part of daily work" — never defer all cleanup to a "refactoring sprint" [GROUNDED].  
- Small safe edits are composable and reversible; large transformations hide risk [USER-GROUNDED].

### Decision Heuristics

- **Primary Directive**: Before any change, ask "What makes this change awkward?" and "What local structural change would make it straightforward?" [USER-GROUNDED].  
- **Two Hats / Intent Separation**: Never mix structural edits with behavior changes. First land pure refactor PR (zero behavior change), *then* semantic PR. Single-commit rule: title must be purely "refactor:", "feat:", "fix:", or "chore:". PR checklist: "Does this contain *only* one intent?" [USER-GROUNDED].  
- **Micro-PR Pipelining**: Split into atomic, stackable PRs (e.g., rename → extract → feature). If patch >30 LOC or feels too large to reason about locally, split immediately [USER-GROUNDED].  
- **Diff-Symmetry Rule**: If refactoring PR changes test *assertions* (not just setups), reject — it proves behavioral drift [USER-GROUNDED].

### Commitment Thresholds

Commit to refactoring **only when** the requested change becomes easy to implement, the main smells blocking it are removed, and readability/local changeability are clearly improved [USER-GROUNDED].  

- **Broad refactoring threshold**: High churn-complexity (>8 changes/90d), low coupling, roadmap alignment within 1 quarter, and ADR approval.  
- **Micro-refactoring threshold**: Single-file, <15 min, zero public API change, existing tests cover it — execute inline under Boy Scout Rule.  
- **Documented deferral threshold**: Zero upcoming roadmap entries, low churn (<3 changes/18mo), verification confidence <90% — write TODO + tech-debt ticket with explicit EOL date; do not touch.  
  Never introduce interfaces, strategy hierarchies, or common libraries before a *second real need appears* [USER-GROUNDED]. If further cleanup becomes speculative, stop immediately.

### Anti-Patterns

- **Mixed-Intent Patches**: Bundling behavior change with structural churn (makes review impossible and regressions invisible) [USER-GROUNDED].  
- **Big-Bang Rewrite**: Replacing a working subsystem wholesale without first understanding current behavior via safety net [USER-GROUNDED].  
- **Refactoring Theater**: Renaming, adding wrappers, or cosmetic layers while deeper design problems remain untouched [USER-GROUNDED].  
- **Untested Structural Surgery**: Large refactoring without characterization tests or safety net [USER-GROUNDED].  
- **Split-Brain State**: Abandoning refactor 70% complete, leaving competing patterns (doubles cognitive load) [USER-GROUNDED].  
- **Refactoring Horizon Blindness**: Optimizing code slated for replacement by parallel team or managed service [USER-GROUNDED].  
- Aesthetic over-refactoring on low-churn, high-blast-radius, or near-retirement code.

### Uncertainty Handling

Treat every proposed cleanup as a hypothesis. First step: "Create or identify a safety net before risky refactoring" [USER-GROUNDED].  

- No tests or unclear behavior → write characterization tests to lock down current state; start with smallest changes and improve testability first.  
- Telemetry/churn gaps → add 30-day probe + canary; default to micro-refactor + explicit "hypothesis: expected churn reduction X%; revert if telemetry delta < Y within Z days."  
- High-uncertainty paths → Dual-Execution Shadow Routing (run legacy + modern in parallel, assert identical, return legacy until 100k transactions with zero anomalies).  
- Ownership uncertainty → add code-owner annotation + 1-week review buffer. Never ship on stale data (<6mo history) — raise threshold 2× and assume worst-case churn.

### Examples of Judgment

1. **Feature request hits shotgun surgery**: Expert identifies divergent change + high co-change coupling. Applies Preparatory Refactoring (extract method behind interface) in one micro-PR (pure structure). Then lands feature in second PR. Result: change becomes trivial; blast radius minimized.  
2. **Low-churn legacy module with aesthetic smell**: REARF matrix places it in Low-Yield/High-Radius → documented deferral with explicit sunset milestone. No lines touched. Avoids Refactoring Horizon Blindness.  
3. **Unclear behavior in financial engine**: Writes characterization tests, implements shadow routing with telemetry.assertIdentical, gathers production data for two weeks before committing to modern path. Stops at first anomaly.

### Grounding Notes

All sections [USER-GROUNDED] from provided expertise fusion + Fowler preparatory refactoring TYPE-R. Quantitative signals carried as principal-level synthesis. No inference required. Validate with `skills-ref validate ./disciplined-code-refactoring-policy`.
