---
name: reality-grounded-ai-verification
description: Activate this skill for any AI code generation, debugging, refactoring, autonomous agent execution, forensic investigation, or stateful operation involving LLM outputs, tests, logs, 200 OK responses, or non-deterministic inputs. Trigger keywords: source of truth, full state verification, forensic investigation, claim-verdict conflation, before-after delta, zero-trust execution, linear sequential unmasking. Use whenever model-generated intent must be proven against physical reality rather than accepted as narrative.
---

### Activation

Trigger this skill immediately upon any of the following:

- LLM or AI agent proposes or executes code that mutates state (database rows, files, queues, memory).
- Debugging, refactoring, or forensic investigation of AI-generated artifacts.
- Any test, log, API response, or model CoT is presented as evidence of success.
- Session involves non-deterministic inputs (LLM token streams, external APIs, stochastic engines).

### Expert Salience

Load-bearing situational features are **only** those at the physical state layer: database rows, file bytes on disk, queue messages, syscall traces, cryptographic hashes, and exact before/after deltas.  
Surface signals (passing tests, 95% coverage, 200 OK responses, coherent model CoT, log lines saying “success”) are provisional evidence only — heavily down-weighted as **claims**, never verdicts. [USER-GROUNDED]  

Signal-weighting hierarchy (strict epistemic ordering):

- **Provisional (low weight)**: HTTP 200 OK, coherent CoT/rationale, 100% test pass/coverage, application logs.
- **Authoritative (high weight)**: Physical ledger state (DB rows, file bytes, kernel traces), cryptographic hash equality, external-oracle delta matches.

Weighting shifts instantly when crossing the Deterministic-Stochastic Boundary (any LLM involvement, session length >10 turns, context growth, prior corruption history, or hypothesis entropy spike). In those conditions, surface signals drop to near-zero weight; replay divergence or hash mismatch becomes decisive. [USER-GROUNDED]

### Mental Models

Model the system as a hostile intersection of two incompatible domains:
