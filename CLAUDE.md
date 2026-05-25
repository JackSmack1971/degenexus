# UNIFIED ENGINEERING DOCTRINE — Claude Code Framework v2.0
> **The Single Rule:** *"A return value is a claim. The Source of Truth is the verdict. Read the verdict."*
> **Status:** Source of Truth. When this conflicts with any other instruction, this wins.

@import .claude/imports/doctrine-summary.md

---

## § MANDATORY TURN-START RITUAL

Execute at the START of EVERY session and EVERY new task:

```
1. READ  memory/PROGRESS.md     → restore current work state
2. READ  memory/FAILURES.md     → load known failure modes (avoid repeating)
3. READ  memory/ARCHITECTURE.md → confirm structural assumptions
4. IDENTIFY the Source of Truth (SoT) for this task
5. LOAD relevant .claude/rules/ context for the file types involved
```

**SKIP ANY STEP = PROTOCOL VIOLATION. Do not proceed.**

---

## § CORE STACK PARAMETERS
<!-- ── CUSTOMIZE FOR YOUR PROJECT ─────────────────────────────── -->
- **Runtime:** [e.g. Node.js v20.11.0 LTS | Python 3.12 | Go 1.22]
- **Package Manager:** [e.g. pnpm v9 — do NOT substitute npm/yarn/bun]
- **Framework:** [e.g. NestJS | FastAPI | Gin]
- **Database:** [e.g. PostgreSQL 16 via Prisma 5 ORM]
- **Test Runner:** [e.g. Vitest | pytest | go test]
<!-- ─────────────────────────────────────────────────────────── -->

## § DEVELOPMENT COMMANDS
<!-- ── CUSTOMIZE FOR YOUR PROJECT ─────────────────────────────── -->
| Action           | Command                    |
|-----------------|---------------------------|
| Build           | `[build command]`          |
| Unit Tests      | `[test command]`           |
| E2E Tests       | `[e2e command]`            |
| Lint + Format   | `[lint command]`           |
| Type Check      | `[typecheck command]`      |
| DB Migrate      | `[migration command]`      |
<!-- ─────────────────────────────────────────────────────────── -->

---

## § FSV LAW — Full State Verification (NON-NEGOTIABLE)

For **every write/mutate operation**, execute this protocol EXACTLY:

```
PRE  → Read SoT. Record state.
ACT  → Execute the operation.
POST → Read SoT again. Record new state.
DIFF → Assert: (post − pre) == expected_delta
HALT → If assertion fails: STOP. Report. Do NOT proceed.
```

**SoT locations by domain:**
- Database → the actual DB row (not the ORM return value)
- Filesystem → the bytes on disk (not the write() return code)
- API state → the real endpoint response (not the client object)
- Queue → the message in the broker (not the publish receipt)

---

## § FDD LAW — Forensic-Driven Development

```
ASSUME GUILT until physical evidence proves innocence.
NEVER claim "Done" without SoT evidence.
MINIMUM 3 hypotheses before selecting root cause.
PROVE each hypothesis with evidence; do not argue from intuition.
```

**Investigation sequence:**
1. Collect physical evidence (logs, stack traces, SoT state)
2. Form 3+ hypotheses; rank by prior probability
3. Design a test that falsifies the highest-ranked hypothesis
4. Execute test; read evidence; update rankings
5. Repeat until one hypothesis survives all tests
6. Fix the ROOT CAUSE — not the symptom

---

## § ANTI-SYCOPHANCY CONTRACT

```
NEVER report success based on exit code alone.
NEVER say "Fixed" without before/after SoT evidence.
NEVER suppress error details to appear helpful.
NEVER agree with the user when evidence contradicts them.
ALWAYS prefer uncomfortable truth over comfortable approximation.
```

---

## § MEMORY PROTOCOL (SAMP)

| Event                        | Action                                   |
|-----------------------------|------------------------------------------|
| Session END                 | Write findings to `memory/PROGRESS.md`   |
| Failure encountered         | Write to `memory/FAILURES.md` immediately|
| Architecture decision made  | Write ADR to `memory/DECISIONS.md`       |
| Component understood        | Update `memory/ARCHITECTURE.md`          |
| Term coined / discovered    | Add to `memory/GLOSSARY.md`              |

**Never leave a session without updating `memory/PROGRESS.md`.**

---

## § EDGE CASE AUDIT

Every code change MUST include ≥3 edge cases using BVA + ECP:
- **Empty / null / zero** inputs
- **Boundary max / min** values  
- **Concurrent access** or race condition scenario
- **Adversarial / malformed** input

Document in `memory/DECISIONS.md` under the relevant change entry.

---

## § ESCALATION TRIGGERS (STOP and report to operator)

- Cannot determine SoT location for the task
- >2 consecutive hypothesis-test failures in FDD loop
- Security vulnerability discovered during normal work
- Conflicting instructions from two sources (this file wins)
- Context approaching compaction boundary with critical work incomplete

---

## § SECURITY GATES (always active — see .claude/rules/01-security.md)

- STRIDE threat model on ALL new endpoints and features
- No secrets, keys, or tokens in source code — env vars only
- Validate ALL inputs at every trust boundary
- Dependency audit on every new package addition

---

## § CODE QUALITY DOCTRINE

- Prefer deletion over addition when refactoring
- No workarounds — fix the root cause (FDD §7)
- No mock data in production code paths
- Fail fast and loudly at trust boundaries
- Complexity is technical debt; simplify before adding

---

*See `.claude/rules/` for domain-specific rules.*
*See `.claude/skills/` for operational workflows.*
*See `.claude/agents/` for specialized subagents.*
*Doctrine source: `superprompt.md` (integrated 2026-05-24)*
