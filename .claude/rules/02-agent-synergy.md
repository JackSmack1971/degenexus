# Agent-Skill Synergy Map

Use this map as the single routing source for `/audit`, `/review`, `/ship`, and specialist handoffs.

| Trigger | Primary agent | Supporting skill(s) | Required evidence |
| --- | --- | --- | --- |
| `.claude/**`, `CLAUDE.md`, `AGENTS.md`, memory, issue, or PR-template changes | `docs-memory-curator` | `claude-config-audit`, `release-evidence-pack` | Config validation output, hook compile output, stale reference scan, memory impact. |
| Prompt construction, LLM context, agent prompts, cross-agent summaries, or untrusted text in prompts | `prompt-injection-auditor` | `prompt-safety-review`, `edge-case-audit` | Trust-boundary trace, sanitizer evidence, regression coverage, unresolved prompt-flow gaps. |
| Security, authentication, secrets, dependencies, or dependency manifest changes | `security-auditor` | `prompt-safety-review`, `dependency-audit`, `claude-config-audit` | Secret scan status, dependency audit evidence, Critical/High vulnerability assessment, remediation owner. |
| Risk gate, execution gate, portfolio exposure, sizing, stop-loss/take-profit, or stale `RiskDecision` behavior | `risk-gate-verifier` | `risk-control-audit`, `fsv-verify`, `edge-case-audit` | PRE/POST source-of-truth reads, rejected bypass paths, edge-case coverage. |
| Trade lifecycle, partial close, terminal state, audit table, or SQLite state | `trade-lifecycle-auditor` | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` | Direct SQLite row deltas, restart durability impact, lifecycle invariant proof. |
| Market data, yfinance, OHLCV, indicator warmup, fallback feed, NaN, or network degradation | `market-data-integrity-auditor` | `edge-case-audit`, `fsv-verify` | NaN/warmup/network cases, fallback proof, source-of-truth data comparison. |
| Bug persists after the first fix or evidence is contradictory | `fdd-investigator` | `forensic-debug`, `fsv-verify` | Hypotheses, falsification results, 5-Whys root cause, source-of-truth proof. |
| Test authoring, coverage gaps, regression tests, or Prove-It failures | `test-engineer` | `test-regression`, `edge-case-audit`, `fsv-verify` | Failing-before/passing-after evidence, FSV-AAA assertions, at least three edge cases. |
| Merge readiness | `ship` as main-session coordinator or parent-session fan-out prompt | `release-evidence-pack`, `claude-config-audit` | GO/NO-GO, command evidence, specialist summary, blockers, memory-update status. |

## Output contract for every routed review

- Scope reviewed.
- Source of truth used.
- Specialists and skills invoked, or a reason each applicable specialist was skipped.
- Evidence commands and exact results.
- Findings by severity.
- At least three edge cases considered.
- Memory update needed: yes/no plus path.
- Next action owner.
