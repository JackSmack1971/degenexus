---
name: forensic-driven-development
description: >
  Diagnose production incidents, persistent bugs, and unexpected system behaviors
  through forensic reasoning rather than surface debugging. Apply crime-scene
  preservation, timeline reconstruction, multi-hypothesis falsification,
  Swiss-cheese failure analysis, and AI-generated assumption audits to distinguish
  proximate symptoms from verified root causes. Trigger on: production incident,
  root cause analysis, RCA, post-mortem, persistent bug, forensic debugging,
  incident investigation, failure diagnosis, FDD, unexpected behavior, causal
  chain, recurrence risk, layered failure, generated code failure.
compatibility: >
  Targets staff/principal-level investigators with working knowledge of distributed
  systems observability: logs, traces, metrics, deployment history, incident
  response. Does not teach basic debugging or observability tooling.
---

## Activation

Invoke when:

- A production incident requires root cause identification beyond surface triage
- A persistent or intermittent failure resists ordinary debugging
- An unexpected system behavior cannot be explained by local inspection
- A post-incident review must distinguish proximate cause from systemic contributors
- Generated or AI-assisted code is in the failure path
- An incident was "resolved" but recurrence risk has not been formally assessed

Do not invoke for routine defects that are observable, reproducible, and locally isolated with no systemic indicators.

---

## Expert Salience — Load-Bearing Features

Attend to these before any others. They carry the most causal weight.

**Highest salience — always assess first:**

1. **Timeline before symptom onset** — What changed, deployed, or shifted in the window before the failure? Causal events precede symptoms; signals at symptom-time are often effects, not causes.
2. **Evidence chain independence** — Are ≥2 independent sources supporting the same narrative? Single-source explanations are provisional by definition.
3. **Hypothesis count** — How many competing hypotheses remain active? Prematurely collapsing to one is the primary cognitive failure mode in this domain.
4. **Generated/AI-assisted code involvement** — If the failure path touches AI-generated implementation, apply the AI-Generated Assumption Audit immediately.
5. **Scope indicators** — Retries, timeouts, leader elections, failovers, cross-service errors → cross-system scope. Resource exhaustion, config drift, race conditions, local observability gaps → single-service scope.
6. **Causal chain completeness** — Has the mechanism been explained (not just located)? A proximate defect without a mechanism is a symptom description.
7. **Detection and control gaps** — Where did observability fail to surface the failure earlier? Where did safeguards fail to contain it?

**Deprioritize:**

- Dashboard summaries without raw signal verification
- Human-written incident notes as primary evidence (treat as low-provenance hypothesis inputs)
- Patch success as causal confirmation

---

## Mental Models

### 1. Crime-Scene Preservation

Before any remediation, snapshot volatile state: in-memory data, process state, active connections, current metric windows, log buffers. Remediating before preserving destroys direct causal evidence. Start every investigation with: *What evidence will be destroyed by the next action?*

### 2. Timeline Reconstruction

Build a precise chronological sequence from all sources: deploys, config changes, traffic patterns, alerting events, log timestamps, infrastructure events. The causal event is typically upstream of the first visible symptom. Timeline gaps are findings, not absences of data.

### 3. Multi-Hypothesis Falsification

Generate ≥3 competing hypotheses before investigating any one. For each, identify what evidence would *falsify* it — not merely support it. Work to falsify, not confirm. Confirmation bias is the primary cognitive threat in incident investigation.

### 4. Swiss-Cheese Failure Model

Production failures rarely have a single cause. They require multiple latent weaknesses (holes in Swiss-cheese layers) to align simultaneously. When a plausible proximate cause appears, ask: *What pre-existing conditions made this defect catastrophic rather than recoverable?* Traverse all six layers: triggering event → proximate defect → latent conditions → design defect → detection gap → control gap.

### 5. AI-Generated Assumption Audit

When generated or AI-assisted code is in the failure path, systematically enumerate hidden assumptions introduced during generation. Ask: *What must be true for this generated code to behave correctly in production, and which assumptions are false, unproven, or production-sensitive?*

Common AI-generated assumption classes to enumerate:

- Single-node execution (no distributed coordination assumed)
- Idempotent retries (retry safety not verified against endpoint)
- Clock synchronization (timestamps treated as reliable ordering signal)
- Local cache invalidation (no cross-node coherence assumed)
- Rare or irrelevant leader changes
- Concurrency coverage in generated tests
- Deterministic dependency responses
- Prompt intent equals implementation behavior
- Observability exists at the failure boundary
- Local reproduction captures production topology

Audit process: extract assumptions → classify each as *proven*, *unproven*, or *falsified* → treat falsified assumptions as causal candidates. An LLM may assist enumeration, but the investigator verifies each assumption against evidence.

### 6. Signal Provenance Hierarchy

Default ranking from highest to lowest provenance (least-transformed to most-transformed):

1. Packet captures / wire-level evidence
2. Kernel, host, container, runtime telemetry
3. Orchestration events
4. Database / storage state
5. Distributed traces
6. Structured application logs
7. APM summaries and dashboards
8. Human-written notes and assumptions

**Inversion conditions** — application-layer may outrank infrastructure-layer when:

- Failure mechanism is semantic rather than transport-level
- Business logic state explains behavior infrastructure cannot observe
- App emits deterministic domain events with strong correlation IDs
- Infrastructure metrics are sampled, aggregated, delayed, or lossy
- Lower-layer signal confirms transport success but app violates consistency, ordering, authorization, or cache-invalidation rules

**Principle:** prefer the least-transformed signal closest to the disputed mechanism. [USER-GROUNDED]

### 7. Recurrence-Risk Taxonomy

Classify every confirmed root cause across all six tiers:

| Tier | Label            | Description                                                                 |
| ---- | ---------------- | --------------------------------------------------------------------------- |
| 1    | Triggering event | The immediate event that exposed the failure                                |
| 2    | Proximate defect | The local mechanism producing the visible symptom                           |
| 3    | Latent condition | The pre-existing weakness that made failure possible                        |
| 4    | Design defect    | The architectural or protocol flaw that will recur under related conditions |
| 5    | Detection gap    | Why the system failed to detect or contain the issue earlier                |
| 6    | Control gap      | Why safeguards did not prevent recurrence                                   |

A root cause report addressing only tiers 1–2 is incomplete.

---

## Thinking Rules

1. **Plausible ≠ confirmed.** When a plausible local cause appears, treat it as one hypothesis in the active set, not as the root cause. Production failures emerge from layered latent conditions interacting across time. [USER-GROUNDED]

2. **Causal chains, not locations.** The goal is explaining *how* the failure occurred, not merely *where* it manifested. A location without a mechanism is a symptom description.

3. **Provenance determines weight.** Lower-layer, less-interpreted signals outrank higher-layer summaries by default. Invert only when the mechanism is semantic and the application-layer signal is closer to the disputed behavior. [USER-GROUNDED]

4. **Absence of signal is a signal.** Gaps in logs, traces, or metrics are findings. They indicate either that the failure occurred outside instrumented boundaries or that observability infrastructure is part of the failure surface.

5. **Remediation ≠ validation.** A patch that removes a symptom does not confirm the causal model. A different mechanism can produce identical symptoms; removing the proximate trigger may mask the latent condition. [USER-GROUNDED]

6. **Timeline consistency is mandatory.** Any proposed cause that postdates its alleged effect, or that contradicts the observed event sequence, is falsified regardless of other support. [USER-GROUNDED]

---

## Decision Heuristics

**When to expand from single-service to cross-system scope:**

- Retries, timeouts, circuit breakers, or cascading errors are present
- Leader election, failover, or topology change occurred in the investigation window
- Multiple services exhibit correlated anomalies without a common local cause
- The proximate defect alone cannot explain the blast radius

**When infrastructure signal conflicts with application signal:**

- Default: weight infrastructure signal higher (lower provenance tier)
- Invert if: transport is confirmed successful AND the failure is semantic (ordering, auth, consistency, cache coherence)
- Decision rule: *Which signal is least-transformed and closest to the disputed mechanism?*

**When to apply AI-Generated Assumption Audit:**

- Any generated or AI-assisted code is in the failure path
- The defect cannot be explained by the visible implementation logic alone
- The failure is intermittent, environment-specific, or topology-dependent

**When recurrence-risk assessment is complete:**

- Recurrence risk remains *unresolved* until tiers 3–6 have been explicitly assessed
- Recurrence-risk grades [USER-GROUNDED]:
  - **Low**: deterministic defect removed, alternatives falsified, regression test added, observability confirms absence
  - **Medium**: proximate cause fixed; latent conditions or detection gaps remain
  - **High**: symptom patched; causal chain incomplete; systemic contributors unaddressed
  - **Critical**: failure mechanism is architectural, probabilistic, cross-system, or amplified by generated-code assumptions

---

## Commitment Thresholds

A root cause may be declared only when a **verified causal chain** is established. Plausible explanation is not sufficient. [USER-GROUNDED]

**Required together in normal FDD work:**

1. **Timeline consistency** — proposed cause precedes effect; observed sequence fully explained without contradiction
2. **Evidence convergence** — ≥2 independent sources support the same causal narrative (e.g., traces + orchestration events; logs + network captures; metrics + git history)
3. **Competing-hypothesis falsification** — all major alternatives explicitly tested and rejected with distinct evidence
4. **Mechanism explanation** — root cause explains *how* the failure occurred, not merely *where*

**Sufficient alone (rare):** Only when direct deterministic evidence is available — e.g., a crash dump proving a specific invalid memory access causally tied to a specific deployed change.

**Strengthens but does not substitute:** Remediation validation or controlled reproduction increases confidence but does not replace requirements 1–4. A patch can suppress a symptom while leaving the causal model wrong.

**If thresholds are not met:** remain provisional. Document which criterion is unmet and what evidence would satisfy it. Declare *working hypothesis*, not *root cause*.

---

## Anti-Patterns

**Symptom fixation** [USER-GROUNDED]
Patching the visible failure while leaving the causal chain, systemic contributors, and recurrence risk unresolved. A fix that removes the symptom without traversing the full recurrence-risk taxonomy is symptom management, not root cause resolution.

**Single-line-diff closure** [USER-GROUNDED]
Attributing the entire failure to one recent code change without verifying it is a sufficient causal explanation. Recent diffs are high-salience candidate hypotheses — not confirmed causes.

**Single-source evidence**
Committing to a root cause supported by only one evidence source. All single-source conclusions are provisional by definition.

**Premature hypothesis collapse**
Reducing the active hypothesis set to one before competing hypotheses have been falsified with distinct evidence. Generate ≥3 hypotheses before investigating any.

**Remediation-as-confirmation** [USER-GROUNDED]
Treating a successful patch as proof of the causal model. A different latent mechanism can produce identical symptoms; suppressing the proximate trigger may mask the deeper failure.

**Recurrence-risk truncation** [USER-GROUNDED]
Closing an investigation after addressing only tiers 1–2 (triggering event, proximate defect) without assessing latent conditions, design defects, detection gaps, and control gaps (tiers 3–6).

**AI-assumption blindness** [USER-GROUNDED]
Failing to apply the AI-Generated Assumption Audit when generated code is in the failure path. Generated implementations carry implicit assumptions that are invisible in code review and frequently invalid in distributed production environments.

---

## Uncertainty Handling

**When evidence is missing:**

- Treat gaps as findings — document what is absent and what it would have explained
- Do not infer that a mechanism did not occur merely because no signal captured it
- Identify whether the gap indicates observability failure or genuine absence of the event

**When signals conflict:**

- Apply the Signal Provenance Hierarchy; default to least-transformed
- If inversion conditions apply, explicitly state the inversion reasoning and which condition triggers it
- Document both signals and the weighting decision in the causal narrative

**When timeline is ambiguous:** [INFERRED — distributed systems principles]

- Clock skew, aggregated metrics, and sampled telemetry introduce false sequence ordering
- Treat timestamps from distributed sources as approximate unless confirmed synchronized
- Use ordering from a single authoritative source (WAL, event log, packet sequence numbers) where available

**When the hypothesis set cannot be reduced:**

- Remain provisional; state what additional evidence would falsify each remaining hypothesis
- Do not declare a root cause; declare competing working hypotheses with explicit falsification criteria
- Under time pressure, classify the conclusion explicitly as *best available hypothesis* with outstanding falsification requirements documented

**When AI-generated assumptions cannot be verified:**

- Classify each unverifiable assumption as high-risk latent condition
- Escalate to design review; do not treat unverifiable as benign

---

## Examples of Judgment

### Case 1: Cache invalidation failure after leader failover

**Symptom:** Stale reads on read replicas after leader failover.
**Initial hypothesis (low-salience anchor):** Replication lag — infrastructure issue.

**FDD reasoning:**

- Timeline: failover event 200ms before first stale read → causal window established
- Infrastructure signal (replication metrics): normal lag, no queue backup → *falsifies replication-lag hypothesis*
- Application trace: invalidation calls present but scoped to old leader endpoint
- Provenance inversion applied: transport layer confirms success; application event log is closer to disputed mechanism (cache coherence scope binding)
- Latent condition (tier 3): invalidation assumes leader-endpoint stability
- Design defect (tier 4): cache coherence depends on implicit leader stability
- Detection gap (tier 5): no alert on stale-read rate; no trace span around invalidation scope

**Commitment decision:** All four criteria met — timeline consistent, two independent chains (traces + orchestration events), replication hypothesis falsified, mechanism explained. Root cause declared.

**Recurrence risk:** Critical — leader-endpoint scoping is an architectural assumption that will recur under any failover.

---

### Case 2: AI-generated retry logic — duplicate insertions

**Symptom:** Duplicate order insertions during upstream timeout events.
**Initial hypothesis:** Upstream timeout not handled — implementation bug.

**FDD reasoning:**

- AI-Generated Assumption Audit applied: generated retry code assumes idempotent operations
- Assumption falsified: order insertion endpoint has no idempotency key; retries are non-idempotent in production
- Timeline: upstream timeout (trigger) → retry fired → duplicate insert (proximate defect) → no deduplication guard (latent condition) → no generated test covered concurrent retry behavior (control gap)
- Competing hypothesis (DB-layer race condition): falsified via sequence log showing clean serial inserts; second insert is explicit retry, not concurrent write

**Commitment decision:** All four criteria met. Root cause: generated implementation assumed idempotent retries; production endpoint does not enforce idempotency.

**Recurrence risk:** High — latent condition (no idempotency enforcement) is systemic; any retry path hitting this endpoint will fail identically.

---

## Grounding Notes

All reasoning blocks are [USER-GROUNDED] from expert elicitation (state block, Q1–Q5). No external documentation was consulted during drafting.

External framework attributions for verification:

- Swiss-Cheese Model: Reason, J. (1990). *Human Error.* Cambridge University Press.
- Failure taxonomy structure: informed by STAMP/STPA (Leveson, 2011) and layered accident analysis literature. [INFERRED attribution]
- Hypothesis falsification methodology: Popper's falsificationism applied to systems debugging. [INFERRED attribution]

Blocks requiring external source strengthening for high-stakes deployment:

- `uncertainty_handling` — clock-skew section is [INFERRED] from distributed systems principles; verify against target infrastructure documentation
- `thinking_rules` rule 3 provenance ordering — [USER-GROUNDED] operationally but lacks peer-reviewed citation for the specific hierarchy order
