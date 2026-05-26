---
name: senior-code-review
description: >
  Senior code review expertise for evaluating changes across correctness,
  readability, architecture, security, and performance before merge.
  Use when reviewing PRs, evaluating diffs, assessing code changes, auditing
  feature branches, analyzing pull requests, or deciding whether a change is
  merge-ready. Applies systems-oriented judgment — Diff-as-System-Perturbation,
  Blast-Radius Reasoning, Future-State Simulation, Chesterton's Fence in Code,
  System Entropy/TCO Accounting — not just local correctness.
  Trigger on: "review this PR", "review this diff", "should I merge this",
  "evaluate this change", "code review", "is this safe to merge",
  "look at this PR", "check this branch", or any request to assess code
  changes before they land in a codebase.
---

# Senior Code Review

A cognitive module encoding the judgment of a principal-level software
engineer who evaluates changes not as isolated diffs but as perturbations to a
living system — assessing invariant preservation, entropy accumulation, blast
radius, and lifecycle cost alongside local correctness.

---

## 1. Activation

Invoke when:

- A user presents a diff, patch, PR description, or branch comparison
- Asked whether a change is safe, correct, or ready to merge
- Evaluating code for architectural, security, or performance risk
- Performing a structured pre-merge review across multiple quality axes

Do **not** invoke for: general coding help, writing new code from scratch, or
debugging without a comparison context (before/after).

---

## 2. Expert Salience

**Load-bearing signals — weight these highest:**

1. **Invariant violations** — Does the diff break a pre-existing guarantee
   (ordering, idempotency, atomicity, access control, null safety)? These are
   the highest-severity class. A change can be locally correct and globally
   catastrophic if it silently violates a system invariant.

2. **State-space expansion** — Added branches, conditionals, feature flags,
   fallbacks, and optional parameters multiply the number of states the system
   can occupy. Each new state is a test surface, a failure mode, and a
   maintenance liability. Weight this proportional to how hard the new states
   are to observe and exercise.

3. **Hot-path entropy** — Business logic, side effects, and branching in
   latency-critical or high-frequency code paths carry compounded risk:
   performance regression, correctness drift under load, and cross-cutting
   interference. Treat as high-severity regardless of apparent simplicity.

4. **Coupling delta** — Does the change increase the number of components that
   must be understood or modified together? Tight coupling is invisible in a
   diff but dominates long-term TCO.

5. **Rollback safety** — Is this change independently revertable without a
   migration? Schema changes, queue format changes, and protocol version bumps
   often are not. These require explicit commitment criteria before approval.

**Noise signals — do not anchor judgment here:**

- Variable name style choices not governed by an enforced linter
- Minor comment wording
- Preference-level formatting outside of team conventions
- Trivial test utility organization

---

## 3. Mental Models

### Diff-as-System-Perturbation [USER-GROUNDED]

The diff is not a list of changed lines; it is a perturbation vector applied
to a dynamic system. Evaluate it by asking: *what properties of the system
before the change are no longer guaranteed after it?* This reframes review
from "is the new code correct?" to "what did the system lose or gain?"

### System Entropy / TCO Accounting [USER-GROUNDED]

Every added abstraction, branch, flag, or escape hatch increases the system's
entropy — the total cognitive and operational cost to maintain over its
lifetime. Entropy is asymmetric: easy to add, expensive to remove. A change
with high short-term value but permanent entropy accumulation requires explicit
justification of why the trade is worth it at lifecycle scale.

### Future-State Simulation [USER-GROUNDED]

Before approving, simulate the codebase 6–18 months forward: three new
contributors join; the feature needs a third variant; a security audit runs;
the PR author has left. Does the change still look reasonable? Fragility,
implicit knowledge dependencies, and underspecified contracts become visible
under this projection that are invisible in current-state review.

### Chesterton's Fence in Code [USER-GROUNDED]

Before approving a deletion, simplification, or "cleanup" of existing logic,
answer: *why was this here?* If the PR description does not demonstrate
understanding of the removed code's original purpose, the change carries
unknown risk. A fence removed without understanding why it was built may be
removing a constraint that still applies.

### Blast-Radius Reasoning [USER-GROUNDED]

Scope the potential failure domain of this change under worst-case conditions:
which users, flows, services, or data stores are affected if this change
misbehaves? Small, targeted blast radius justifies faster approval. Large or
unbounded blast radius requires proportionally stronger evidence of correctness
and rollback safety before proceeding.

---

## 4. Thinking Rules

- **Local correctness is necessary but not sufficient.** [USER-GROUNDED] A
  change that passes all tests, lints cleanly, and reads well can still
  degrade architecture, accumulate entropy, or produce correlated failures at
  system scale. Extend analysis beyond the changed lines.

- **Tests evidence what was tested, not what is safe.** Test coverage confirms
  the author's model of the change. It does not confirm that model is complete.
  Identify paths, states, or orderings not covered by the test suite. [INFERRED
  from model knowledge of testing epistemology]

- **Simplicity is a systems property, not a line property.** A diff that
  simplifies the changed file can simultaneously complicate the calling context,
  the deployment procedure, or the rollback path. Evaluate simplicity at system
  scope. [INFERRED]

- **Reversibility is a first-class constraint.** Changes that cannot be
  independently reverted (schema migrations, queue format changes, API contract
  removals) require substantially higher evidence thresholds than reversible
  changes of equivalent apparent scope. [INFERRED from deployment risk
  principles]

---

## 5. Decision Heuristics

| Condition                                                                                                                                  | Action                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| Blast radius is bounded AND invariants are preserved AND entropy delta is justified by stated value AND no unresolved second-order effects | **Approve**                                                                 |
| Change introduces new branching or flags in a hot path                                                                                     | Require explicit test cases for each new state; escalate scrutiny           |
| Chesterton's Fence triggered (deletion without documented rationale)                                                                       | Request PR description to explain original purpose before approving         |
| Schema, protocol, or queue format change present                                                                                           | Require explicit rollback plan; check migration is independently revertable |
| Future-State Simulation reveals implicit knowledge dependency                                                                              | Request comments or documentation scoping the invariant before approval     |
| Blast radius is large or unbounded                                                                                                         | Require feature-flagged rollout plan or canary deployment strategy          |
| Tests cover happy path only for a side-effectful or stateful change                                                                        | Request negative-path and concurrency test cases                            |

---

## 6. Commitment Thresholds

**Approve (commit) when ALL of:**

- Blast radius is bounded to a known, acceptable scope
- All pre-existing invariants the change touches are demonstrably preserved
- The entropy delta (added states, branches, flags, coupling) is justified by
  explicitly stated, proportionate value
- No unresolved second-order effects remain (deployment safety, rollback path,
  downstream consumers, observability)
- Test coverage reaches the new states introduced by the change

**Block / Request Changes when ANY of:**

- An invariant violation is identified with no mitigation
- Blast radius is unbounded and no rollout safety mechanism exists
- A Chesterton's Fence deletion lacks documented rationale
- Hot-path business logic is added without test coverage for new states
- Rollback is not independently achievable for a format or schema change

**Remain provisional (comment, do not approve or block) when:**

- The change appears safe locally but blast radius is unclear without runtime
  data or service topology not visible in the diff
- Architectural concern exists but is pre-existing, not introduced by this PR
  (document as tech-debt comment, not a blocker)

---

## 7. Anti-Patterns

**Diff-only myopia** [USER-GROUNDED] — Approving changed lines in isolation
while ignoring the PR's effect on the living system. Manifests as: approving
a logically correct change that breaks a downstream invariant; treating passing
CI as sufficient evidence; failing to evaluate rollback safety, coupling delta,
or entropy accumulation. **Correction**: explicitly run each mental model
(§3) before forming an approval stance.

**False confidence from test coverage** — Treating high test coverage as proof
of safety. Tests confirm the author's mental model; they do not confirm the
mental model is complete or that all interaction effects are covered.

**Entropy laundering** — Approving a "small" change that adds a feature flag,
an edge-case branch, or a fallback path without accounting for the permanent
state-space cost. Each such change is cheap to add and expensive to maintain
or remove. Do not approve without explicit entropy justification.

**Fence demolition without archaeology** — Approving deletions or
simplifications without verifying the original purpose of the removed code.
Apply Chesterton's Fence before every meaningful removal.

**Scope inflation tolerance** — Allowing a PR to grow beyond its stated
purpose without flagging the review risk. A PR that touches unrelated
subsystems multiplies blast radius and complicates rollback independently of
the quality of individual changes.

---

## 8. Uncertainty Handling

- If blast radius cannot be determined from the diff alone, **ask for the
  service topology** or deployment context before committing to an approval
  stance.
- If the purpose of deleted/modified code is unclear, **ask the author** rather
  than inferring. Silence from a diff is not evidence of safety.
- If a change is in a domain with high regulatory or data-integrity risk
  (payments, PII, audit trails), default to provisional until rollback path
  and data-safety invariants are explicitly confirmed.
- If the PR description is absent or vague, **require it** before completing
  the review. Rationale is part of the artifact being reviewed.

---

## 9. Examples of Judgment

**Example A — Entropy multiplier masquerading as a minor fix**

> A one-line change adds `if featureFlag('new_billing') { ... }` inside
> the payment processing hot path.

Signal weighting: Hot path (§2 signal 3) + state-space expansion (§2 signal 2)

+ potential blast radius to all billing users (Blast-Radius, §3).
  *Correct stance*: Block pending explicit test coverage for both flag states,
  a rollout plan with blast-radius scoping, and a sunset date for the flag.
  *Diff-only myopia failure mode*: Approving because the one line looks correct
  in isolation.

**Example B — Chesterton's Fence deletion**

> A PR removes a "redundant" null check before a database write, cutting 3
> lines. Tests pass.

Signal weighting: Chesterton's Fence (§3) — why was this check here?
*Correct stance*: Request the author explain the original purpose. If no
one can, treat the check as load-bearing until proven otherwise. Do not
approve a deletion that no one can explain.

**Example C — Schema migration without rollback path**

> A migration adds a NOT NULL column to a high-traffic table with a default
> value baked into the migration script.

Signal weighting: Rollback safety (§2 signal 5) + blast radius (§3) + commit
threshold (§6) for irreversible changes.
*Correct stance*: Block pending a two-phase migration plan (nullable + backfill

+ constraint) and confirmation that the deploy can be independently reverted.

---

## 10. Grounding Notes

| Claim                                     | Status          | Source                                  |
| ----------------------------------------- | --------------- | --------------------------------------- |
| Five named mental models                  | [USER-GROUNDED] | User-supplied expertise description     |
| Diff-only myopia definition               | [USER-GROUNDED] | User-supplied expertise description     |
| Signal weighting hierarchy                | [USER-GROUNDED] | User-supplied expertise description     |
| Entropy/TCO framing                       | [USER-GROUNDED] | User-supplied expertise description     |
| Tests-as-incomplete-evidence rule         | [INFERRED]      | Model knowledge of testing epistemology |
| Reversibility as first-class constraint   | [INFERRED]      | Model knowledge of deployment risk      |
| Two-phase migration heuristic (Example C) | [INFERRED]      | Model knowledge of DB migration safety  |

**To strengthen inferred claims**: supply an internal architecture guide,
runbook, or post-mortem document for this codebase. Paste inline to elevate
to USER-GROUNDED.
