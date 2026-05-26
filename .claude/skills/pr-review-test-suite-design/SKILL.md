---
name: pr-review-test-suite-design
description: >
  Evaluates PR test suites as adversarial probes against system-level behavioral
  contracts — not as proof-of-work for touched lines. Use when reviewing tests in
  a pull request, assessing test coverage adequacy, designing missing tests, auditing
  regression gaps, analyzing suite CI health economics, or when asked to: review
  tests, check coverage, assess test strategy, evaluate test quality, validate
  regression coverage, audit test suite health, or determine if a PR needs more
  tests. Applies Blast Radius Mapping, Invariant Preservation + Falsification,
  Behavioral Contract / Encapsulation Boundary reasoning, Suite Health Economics,
  and BVA + ECP Risk Partitioning.
---

## Activation

Invoke when:

- Reviewing a PR that adds, modifies, or deletes tests or tested code
- Assessing whether a PR's test coverage provides genuine safety evidence
- Designing tests for a proposed code change
- Auditing an existing suite for structural weaknesses or maintenance liability
- Evaluating CI health economics or flakiness patterns on a test file

Do not invoke for general code-style review or architecture critique without a
test-design or test-adequacy question attached.

---

## Expert Salience

**Load-bearing signals — weight heavily:**

- Does any test falsify a preserved invariant of the changed subsystem? A suite
  with zero falsifying tests provides zero behavioral safety evidence regardless
  of coverage percentage.
- Does the blast radius of the change extend to a downstream consumer boundary?
  If yes, is that boundary tested?
- Do assertions target observable outputs (return values, persisted state,
  emitted events, HTTP response shape) rather than internal call sequences?

**Secondary signals — necessary but not sufficient:**

- Branch and line coverage metrics — required floor, not a ceiling
- BVA partition coverage on boundary-sensitive logic (numeric ranges, string
  limits, collection edges)
- ECP representative coverage on branching logic (one test per equivalence class)
- Suite economic profile: mock-to-assertion ratio, test body length vs. setup length

**Suppress as noise:**

- "Tests were added" without invariant-to-test mapping
- Coverage percentage reported without blast-radius boundary assessment
- Symmetric test-file-to-source-file parity count

---

## Mental Models

### 1. Blast Radius Mapping [USER-GROUNDED]

Model the PR change as a perturbation originating at a source node. Trace all
reachable paths: direct callers → transitive consumers → public API surface →
downstream system boundaries. The blast radius is the full set of behavioral
contracts that could silently degrade if the change introduces a defect.
Test adequacy is proportional to the fraction of blast-radius boundaries that
have a falsifying test — not to coverage of the changed file.

**Apply:** "What is the furthest boundary this change can reach, and is that
boundary tested against a behavioral violation?"

### 2. Invariant Preservation + Falsification [USER-GROUNDED]

Every non-trivial subsystem has preserved invariants: conditions that must hold
regardless of implementation. Tests provide safety evidence only when they
falsify an invariant — i.e., they would fail if the invariant were broken.
Positive-path tests that always pass regardless of behavioral violations do not
preserve safety; they preserve the illusion of safety.

**Apply:** Identify 1–3 invariants per changed subsystem. Verify at least one
test per invariant would actually fail on a violation.

### 3. Behavioral Contract / Encapsulation Boundary Reasoning [USER-GROUNDED]

A module's contract is its externally observable behavior: inputs → outputs,
preconditions → postconditions, error conditions → recovery behavior.
Tests that pierce the encapsulation boundary (asserting on private state,
verifying internal call sequences) are implementation audits, not contract tests.
Contract tests survive valid implementation changes. Implementation audits do not.
The distinction determines whether the suite is a safety net or a maintenance drag.

**Apply:** Classify each test as contract-level or implementation-level. Flag
implementation-level tests in high-churn modules as economic liabilities.

### 4. Suite Health Economics [USER-GROUNDED]

A test suite has an economic profile: false-positive rate (flakiness + coupling),
maintenance cost per PR, signal-to-noise ratio in CI, and confidence yield per
unit of reviewer attention. Suites with high mock density, deep stub chains, or
assertions that track internal state are economically insolvent — they consume
attention without proportional safety return.

**Apply:** Flag suites where mock setup exceeds ~50% of test body, or where all
assertions are on mock interaction counts rather than output state.

### 5. BVA + ECP Risk Partitioning [USER-GROUNDED]

Boundary Value Analysis (BVA) targets input partition edges where off-by-one and
truncation defects concentrate. Equivalence Class Partitioning (ECP) groups inputs
the system handles identically, requiring one representative per class. Together
they define a minimum sufficient set: one test per partition boundary, one per
equivalence class, one per error partition.

**Apply:** For numeric/range logic, string handling, and collection boundaries,
verify BVA coverage. For branching logic, verify at least one ECP representative
per branch.

---

## Thinking Rules

1. **Locality is not safety evidence.** [USER-GROUNDED] A localized change with
   local tests is not evidence of system safety. Safety evidence requires blast-
   radius boundary coverage. Local correctness does not imply downstream contract
   preservation.

2. **Falsifiability is the unit of test value.** [INFERRED] A test that cannot
   plausibly fail does not provide safety evidence. Every test must have a credible
   failure scenario tied to a behavioral violation, not just a reachable code path.

3. **Real SoT behavior outweighs mocked choreography.** [USER-GROUNDED] Actual
   return values, real state transitions, and integration against a live or
   in-process contract provide stronger evidence than verified call sequences on
   mocks. Mock-heavy suites prove the code calls the right methods; they do not
   prove the methods produce correct behavior.

4. **Tests must survive valid implementation changes.** [USER-GROUNDED] If a
   test breaks on a refactor that preserves behavior, it is implementation-coupled.
   Coupling increases CI noise and degrades trust in red signals over time.

5. **Epistemic default: skeptical and system-oriented.** [USER-GROUNDED] Treat
   every PR as a perturbation to preserved invariants, downstream consumer
   contracts, and CI health. The reviewer's role is adversarial probing, not
   intent-confirmation.

---

## Decision Heuristics

**Request Changes (blocking):**

- Blast radius reaches a downstream consumer boundary AND no test covers that
  boundary against behavioral regression → request contract or integration test
  at the furthest reachable boundary
- A known invariant of the changed subsystem is violated by the change AND no
  test would catch it → request a falsifying test for that invariant
- Entire test suite for a state-mutating change consists of mock-interaction
  assertions with no behavioral output verification → request at least one test
  against real output, final persisted state, or a behavioral contract

**Approve with non-blocking note:**

- Gap is in an adjacent module whose contract is not changed by this PR
- Missing coverage is in a low-probability error partition already covered by a
  higher-level integration test
- PR is explicitly in a provisional implementation phase with a declared follow-up

**Approve silently:**

- Blast radius is fully bounded by tests that would catch behavioral regression
- At least one falsifying test exists per modified invariant
- Tests would survive a pure refactor (low implementation coupling)

**When models conflict — apply this priority order:** [INFERRED]
Invariant Falsification > Blast Radius Boundary Coverage > BVA Partition Coverage

> Suite Health Economics

Suite Health Economics is a debt signal, not a blocking signal. Use it to flag
maintenance liability; do not use it to block a PR with otherwise sufficient
behavioral coverage.

---

## Commitment Thresholds

**Transition to committed block (Request Changes):** [INFERRED]

- When: blast radius includes a published API or downstream consumer, AND no test
  in the suite would detect a behavioral regression at that boundary
- When: a state-mutating operation has no test asserting on final observable state
- When: the only tests present assert solely on mock call counts or argument
  capture, with zero behavioral output assertions, on any non-trivial change

**Remain provisional (investigate before deciding):**

- When: blast radius is ambiguous due to dynamic dispatch, plugin architecture,
  or feature flags — map the radius before concluding
- When: invariant landscape is unclear — identify invariants before ruling coverage
  inadequate
- When: CI flakiness history for the affected test files is unknown — assess
  flakiness before treating failures as behavioral signal

**Hard rule: coverage metrics alone never constitute commitment evidence.**
A coverage percentage without invariant-to-test mapping does not authorize approval.

---

## Anti-Patterns

**Locality Fallacy / Structural Lock-in** [USER-GROUNDED]
Treating local correctness as system correctness. The most common failure mode
in PR review. Testing the changed unit in isolation does not verify that
downstream behavioral contracts remain intact.

**Mock-Call Choreography as Safety Evidence** [USER-GROUNDED]
`expect(dep.method).toHaveBeenCalledWith(x)` verifies execution order, not
behavioral correctness. These tests break on valid refactors and cannot detect
silent output degradation. They prove the right methods were called; they do not
prove those methods produced correct behavior.

**Coverage Theater** [INFERRED]
Reporting line/branch percentages as a proxy for adequacy. High coverage on
trivial paths with no invariant falsification produces false confidence.
Coverage is a necessary floor, not evidence of safety.

**Happy-Path Monoculture** [INFERRED]
Suites dominated by positive-path tests on nominal inputs. Without BVA boundary
tests and error-partition ECP representatives, the suite misses the exact input
regions where defects concentrate.

**Assertion Amnesia** [INFERRED]
Elaborate setup and mock scaffolding followed by `toBeDefined()` or
`not.toThrow()` assertions. Setup complexity without behavioral assertions
is pure overhead — it increases maintenance cost while providing no safety signal.

---

## Uncertainty Handling

**Blast radius is ambiguous (dynamic dispatch, plugins, feature flags):**
Trace call graphs, dependency injection configurations, and event subscription
registries before concluding. Treat any dynamic dispatch boundary as a blast-
radius endpoint until explicitly traced. If the radius cannot be bounded, flag
as an architectural risk and request documentation of the consumer contract.

**Invariant landscape is unknown:**
Ask the PR author to state the preserved invariants of the changed subsystem.
If no invariants can be stated, the subsystem lacks a behavioral contract —
flag as a design gap, not a test gap.

**Conflicting signals between models:**
Apply the priority order: Invariant Falsification > Blast Radius > BVA/ECP >
Suite Health Economics. Suite economics is always secondary.

**CI flakiness history is unavailable:**
Treat new tests as provisionally reliable. Flag that meaningful flakiness
assessment requires ≥20 CI runs before the signal is trustworthy.

---

## Examples of Judgment

**Case 1: High coverage, zero blast-radius coverage**
A pricing calculation module is modified. Unit tests cover 92% of lines. All
tests call the module directly with mocked database dependencies and assert on
return values. The module feeds a billing aggregation service tested in a
separate integration suite.
→ **INADEQUATE.** Local correctness is established; blast-radius boundary is
not covered. The billing boundary can receive a silent behavioral regression
that all 92% of unit tests would miss. Request: one contract or integration
test verifying the billing service receives the expected pricing signal.

**Case 2: Low coverage, strong invariant falsification**
An authentication token validator is refactored. Coverage: 58%. Two tests present:
(1) expired token → 401 with specific error code; (2) structurally invalid token
→ rejected before any database lookup. These directly falsify the two core
invariants of the validator.
→ **ADEQUATE for stated invariants.** Coverage gap exists on edge partitions
(malformed-but-not-expired, valid-structure-but-wrong-algorithm). Non-blocking:
recommend BVA additions in follow-up.

**Case 3: Mock-heavy suite on a state-mutating operation**
An order-processing workflow is modified. 14 tests verify that specific repository
methods were called with specific arguments. No test asserts on final persisted
order state or any observable output.
→ **INADEQUATE.** Tests verify execution choreography, not behavioral correctness.
A bug that calls the right methods with wrong argument data passes all 14 tests.
Request: at least one test verifying final persisted state or equivalent behavioral
output.

---

## Grounding Notes

- Mental models (all five frameworks): [USER-GROUNDED] — user-supplied domain description
- Epistemic stance (skeptical, perturbation-oriented): [USER-GROUNDED]
- Primary anti-pattern (Locality Fallacy): [USER-GROUNDED]
- SoT-over-mock heuristic: [USER-GROUNDED]
- Signal priority ranking: [INFERRED] — derived from framework semantics; confirm in revision
- Commitment threshold conditions: [INFERRED] — derived from invariant and anti-pattern logic
- BVA/ECP application mechanics, economic thresholds: [INFERRED] — standard test design theory

To strengthen: supply an explicit blocking-criteria rubric, a team testing philosophy
doc, or an architecture decision record anchoring the priority hierarchy and
commitment thresholds.
