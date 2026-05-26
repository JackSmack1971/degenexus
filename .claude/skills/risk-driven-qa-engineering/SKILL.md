---
name: risk-driven-qa-engineering
description: Activate this skill whenever defining test strategy, writing/reviewing tests, analyzing coverage reports, evaluating QA suite health, allocating testing effort, or deciding release readiness. Trigger keywords: test strategy, risk-based testing, coverage analysis, failure modes, QA planning, suite health, idempotency, rollback, exactly-once, coverage fallacy.
---

# Risk-Driven QA Engineering

## Activation

Invoke this skill in any context involving test strategy definition, test writing or review, coverage interpretation, suite maintenance, or release-gate decisions—especially under resource constraints or when high-stakes behaviors (payments, state mutations, security, concurrency) are present.

## Expert Salience

Focus exclusively on these load-bearing features (ignore raw line/branch coverage percentages or test volume unless they correlate with them):  

- Consequence of failure (business, user, financial, safety impact).  
- State complexity and implicit contracts (idempotency, rollback safety, authorization, ordering guarantees, exactly-once semantics).  
- Boundary coupling (component interfaces, external services, timing, concurrency).  
- Assertion strength and observability (how reliably incorrect behavior can be detected).  
- Risk signals: likelihood (complexity, churn, newness) × impact.  

Deprioritize or treat as noise: low-impact cosmetic/internal logic, checklist-style verification that does not reduce uncertainty on highest-risk behaviors.

## Mental Models

- **Failure-Mode Economics**: Testing is an economic investment that reduces uncertainty about the most costly potential failures.  
- **Systemic Invariant Reasoning**: Identify and protect the core properties the system must maintain regardless of implementation details.  
- **Suite Health Economics**: Evaluate the entire test suite by its ability to surface real production risk, not by size or execution speed.  
- **Coverage-as-Diagnostic-Not-Target**: Tests and metrics are instruments for gathering actionable information about system behavior under risk, never ends in themselves. [USER-GROUNDED]

## Thinking Rules

- QA expertise is modeled as risk-driven information gathering rather than confirmatory verification. [USER-GROUNDED]  
- Allocate effort strictly by consequence, state complexity, boundary coupling, assertion strength, and observability rather than by raw coverage or test volume. [USER-GROUNDED]  
- Passing tests, green CI, and high coverage are always provisional signals unless they demonstrably reduce uncertainty about the highest-risk behaviors. [USER-GROUNDED]  
- The cheapest reliable test layer is preferred; escalation is required precisely when the risk lives in boundaries, timing, emergent state, or large input spaces.

## Decision Heuristics

- Place tests at the cheapest reliable layer that can exercise the identified risk.  
- Escalate to integration, E2E, exploratory, property-based, chaos, or concurrency testing exactly when the risk resides in boundaries, timing, emergent state, or large input spaces. [USER-GROUNDED]  
- When implicit contracts (idempotency, rollback, authorization, ordering, exactly-once) are involved, prioritize targeted verification over broad low-level unit coverage.  
- Re-evaluate suite health whenever new code changes introduce high consequence or high coupling.

## Commitment Thresholds

Remain in a provisional state (do not commit to release sign-off or declare “done”) until uncertainty about the highest-risk behaviors and implicit contracts has been actively reduced.  
Commit only when targeted verification exists for top risks (failure-mode economics applied) **and** signals such as strong assertions on state transitions, exploratory findings, or failure-injection results confirm reduced uncertainty. [USER-GROUNDED]  
If green CI exists but highest-risk areas lack boundary/observability coverage, treat the signal as provisional and escalate testing.

## Anti-Patterns

- **Coverage Fallacy**: Mistaking code execution, checklist completion, high coverage percentages, or passing tests for evidence that the system behaves correctly under real production risk. [USER-GROUNDED]  
- Treating QA as confirmatory verification instead of risk-driven information gathering.  
- Uniform testing effort across all code regardless of consequence or risk location.  
- Over-reliance on low-level unit tests for risks that only manifest at integration, concurrency, or production-like conditions.  
- Ignoring non-functional or implicit requirements in favor of functional checklist completion.

## Uncertainty Handling

Hold all passing tests, green CI, and high coverage skeptically: they are provisional signals unless they reduce uncertainty about highest-risk behaviors. [USER-GROUNDED]  
When data is missing or contradictory, escalate to the cheapest reliable layer that can probe the specific uncertainty (property-based for large input spaces, chaos for timing, exploratory for unknown unknowns).  
Use failure-mode economics to guide which uncertainties to resolve first; never default to “more tests” without tying them to consequence-weighted risks.

## Examples of Judgment

**Scenario**: Payment processing module with high business impact.  
Expert salience signals: state transitions (cart → order), idempotency of retries, rollback on failure, concurrent purchase races, external gateway coupling.  
Judgment: Deprioritize UI pixel-perfect unit tests; invest heavily in property-based tests for monetary calculations, integration tests for gateway interactions, chaos tests for network partitions, and explicit verification of exactly-once semantics. 90 % unit coverage on internal helpers is noted but does not move the commitment threshold—only the risk-reduced signals do. [USER-GROUNDED + INFERRED structural example]

## Grounding Notes

Entire skill is anchored in the user-provided expertise description [USER-GROUNDED]. All reasoning blocks preserve the exact framing, heuristics, anti-patterns, and uncertainty stance supplied. Minor structural expansions to match SKILL.md schema are [INFERRED] solely to operationalize the provided model while staying faithful to the original text.
