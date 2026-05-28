---
name: fsv-verify
description: Activate Full State Verification (FSV) on every agentic write/mutate operation. Enforce PRE → ACT → POST → DIFF → HALT with adversarial source-of-truth (SoT) decoupling to eliminate tautological verification, context-compaction drift, and automation bias in agentic software engineering.
when_to_use: >
  Use for every write or mutation that needs source-of-truth proof with PRE, ACT,
  POST, DIFF, and HALT evidence.
---

### Activation

Trigger this skill on any agent-initiated mutation: file edits, API calls, ORM updates, schema changes, database writes, cache invalidations, or multi-agent orchestration steps. Also activate on post-mutation verification, CI green signals, or when any tool/actor reports "success" without independent SoT proof. Use when the workflow crosses trust boundaries (worker ↔ evaluator agents) or when context windows may have compacted.

### Expert Salience

Load-bearing features (ranked by epistemic weight):

- **Tier 1 (absolute, weight 1.0)**: Cryptographic hashes of mainnet-replica state, network proxy egress logs, live Kripke-structure equivalence checks.
- **Tier 2 (weight 0.8)**: Adversarial mutation-kill scores (Stryker), AgentVerify LTL/Büchi automaton trace violations.
- **Tier 3 (weight 0.4)**: Fully decoupled evaluator-agent outputs under /goals directive.
- **Tier 4 (weight 0.1, telemetry only)**: Green unit tests, CI coverage, agent self-reports, ORM return values.

Ignore Tier 4 signals until Tier 1–2 are satisfied. The salience budget mathematically blocks progression if Tier 1/2 evidence is absent. [USER-GROUNDED]

### Mental Models

1. **Independent Oracle / Epistemic Decoupling** — The functional generation oracle (worker agent) must be isolated from the constraint verification oracle (evaluator agent or harness). Use /goals directive and proxy monitors the worker cannot detect.
2. **Constraint State Invariance** — Safety constraints are formalized as immutable execution state; they must survive context compaction and never lose operational force.
3. **Forensic Systems Interrogation** — Every mutation is treated as a crime scene: reread authoritative SoT, compute exact deltas, reject any actor that performed the mutation from validating it.
4. **Source-of-Truth Delta Accounting** — Only cryptographic or formally verified deltas between PRE and POST states are admissible proof. [USER-GROUNDED]

These models map directly onto the PRE → ACT → POST → DIFF → HALT sequence for all mutation contexts (single-file, API, ORM, DB schema, multi-agent). [USER-GROUNDED]

### Thinking Rules

- Successful action is never evidence of correct state transition.
- The same cognitive model (or any of its outputs) cannot verify its own mutations.
- Context compaction is inevitable; therefore every constraint must be reified outside the agent’s active buffer (immutable sandbox, proxy logs, replica state).
- Tautological verification collapses under live execution; only independent SoT reread survives adversarial conditions. [USER-GROUNDED]

### Decision Heuristics

- PRE: If mutation detected → isolate worker with /goals; capture SHA-256 hashes of all project files.
- ACT: Route egress through undetectable proxy; enforce LTL bounds at orchestration layer.
- POST: Decouple tests from implementation (generate from OpenAPI spec); run Stryker mutation testing.
- DIFF: Execute AgentVerify Büchi check + localstride mainnet replica hash comparison.
- HALT: If delta magnitude exactly equals pre-approved scope and zero Tier 1/2 violations → merge; else revert and escalate. [USER-GROUNDED]

### Commitment Thresholds

Commit to irrevocable HALT (merge) only when **all** of the following are satisfied:

- Zero HarnessAudit L1/L2 violations and zero LTL Büchi automaton violations.
- ≥80% mutation-kill survival score (tightens to 95% + HITL for Auth/Billing or high-criticality).
- Absolute state-delta match between physical SoT (hashes, schema, tables) and pre-approved scope.
- Stationary mean behavioral drift remains bounded.

Dynamic shifts:

- TPS > 1000 or heavy concurrency → require full distributed container run (no mocks).
- DB schema migration or PII → zero anomaly tolerance; invoke localstride + cryptographic hashes.
- Retry loops exceed max steps → irrevocable HALT, revert, lock harness, escalate to Principal Engineer. [USER-GROUNDED]

### Anti-Patterns

- Tautological Verification Error: trusting the same agent/ORM/mock/CI signal that performed the mutation.
- Context-Compaction Loss: allowing safety constraints to vanish from the active buffer.
- Authority Drift: read-only agents inheriting write privileges through orchestration.
- ORM Abstraction Illusions: assuming synchronous/atomic state when it is not.
- Utility-Induced Drift: deleting legacy tests or skipping cache invalidation to achieve "green" state.
- Information-Flow Drift: leaking PII/keys across agent roles without forensic audit trail. [USER-GROUNDED]

### Uncertainty Handling

When DIFF reveals mismatches:

- **Timestamp / cache staleness** (e.g., 45 ms PostgreSQL drift, Redis TTL lag): Run AgentVerify trace against bounded eventually LTL formula. If convergence is guaranteed without further intervention → ACCEPT-WITH-ANNOTATION (update test tolerance); else RETRY.
- **Concurrent modifications by independent agents** (e.g., security key rotation): Cross-reference orchestration mesh and HarnessAudit logs. If the mutation agent did not cause the change → RETRY (refresh context, re-evaluate); else HALT + revert.
- Any Tier 1 violation or unexplained delta → immediate hard HALT regardless of other signals. [USER-GROUNDED]

### Examples of Judgment

**Example 1 (Timestamp Drift)**: Optimization agent updates retention logic. DIFF shows 45 ms `updated_at` divergence and Redis holding stale objects. Trace confirms safe convergence on TTL expiry → ACCEPT-WITH-ANNOTATION (annotate PR, adjust tolerance to 50 ms). [USER-GROUNDED]

**Example 2 (Concurrent Key Rotation)**: BillingService refactor succeeds but global API keys changed. Audit proves background security agent performed rotation, not optimization agent. Self-tests now stale → RETRY (revert PR, refresh context, re-run). [USER-GROUNDED]

**Example 3 (High-Criticality DB Migration)**: Schema change passes local tests but Tier 1 replica hash mismatch detected. Threshold shifts to zero tolerance → HALT, revert, escalate. [USER-GROUNDED]

### Grounding Notes

All reasoning blocks are [USER-GROUNDED] from Agentic FSV Handbook Development.txt Sections 1–6 and the original FSV description. Structural compliance verified against the Skill Wizard authoring guide. No inference used.
