# Agent-Skill Synergy Map

Use `.claude/rules/synergy-contract.yml` as the machine-readable routing source for `/audit`, `/review`, `/ship`, `/test`, and specialist handoffs. Use this document as the human-readable companion. All routed outputs must satisfy `.claude/rules/evidence-schema.yml`.

| Trigger | Primary agent | Supporting skill(s) | Required evidence |
| --- | --- | --- | --- |
| `.claude/**`, `CLAUDE.md`, `AGENTS.md`, memory, issue, or PR-template changes | `docs-memory-curator` | `claude-config-audit`, `release-evidence-pack` | `config_validation`, `hook_compile`, `stale_reference_scan`, `memory_impact`. |
| Prompt construction, LLM context, agent prompts, cross-agent summaries, or untrusted text in prompts | `prompt-injection-auditor` | `prompt-safety-review`, `edge-case-audit` | `prompt_flow_trace`, `sanitizer_boundary`, `regression_tests`. |
| Security, authentication, secrets, dependencies, or dependency manifest changes | `security-auditor` | `security-review`, `prompt-safety-review`, `claude-config-audit` | `secret_scan_status`, `dependency_audit`, `protected_file_policy`. |
| Risk gate, execution gate, portfolio exposure, sizing, stop-loss/take-profit, or stale `RiskDecision` behavior | `risk-gate-verifier` | `risk-control-audit`, `fsv-verify`, `edge-case-audit` | `pre_state`, `post_state`, `expected_delta`, `rejected_bypass_paths`. |
| Trade lifecycle, partial close, terminal state, audit table, or SQLite state | `trade-lifecycle-auditor` | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` | `sqlite_pre_rows`, `sqlite_post_rows`, `lifecycle_invariant`, `restart_durability`. |
| Market data, yfinance, OHLCV, indicator warmup, fallback feed, NaN, or network degradation | `market-data-integrity-auditor` | `edge-case-audit`, `fsv-verify` | `nan_warmup_cases`, `fallback_proof`, `source_data_comparison`. |
| Bug persists after the first fix or evidence is contradictory | `fdd-investigator` | `forensic-debug`, `fsv-verify` | `hypotheses`, `falsification_results`, `five_whys_root_cause`, `source_of_truth_proof`. |
| Test authoring, coverage gaps, regression tests, or Prove-It failures | `test-engineer` | `test-regression`, `edge-case-audit`, `fsv-verify` | `failing_before`, `passing_after`, `fsv_aaa_assertions`, `edge_cases`. |
| Merge readiness | `ship` as main-session coordinator or parent-session fan-out prompt | `release-evidence-pack`, `claude-config-audit` | `go_no_go`, `command_evidence`, `specialist_summary`, `blockers`, `memory_update_status`. |

## Test-agent ownership

- `test-engineer` is the single canonical test owner for pytest authoring, regression implementation, coverage analysis, and Prove-It/FSV-AAA evidence.
- `test-writer` is a deprecated read-only compatibility alias. It may only redirect older prompts to `test-engineer`; it must not edit files, run tests, or own `/test` routing.
- `/test` routes to `test-engineer` unless a user explicitly asks for a lightweight read-only test-case list, in which case the parent session can answer directly without spawning `test-writer`.

## Security-auditor evidence authority

`security-auditor` remains read-only with no `Bash`. It is an evidence consumer, not a command runner. The parent session or `ship` must provide relevant command output before invoking it, including `python .claude/hooks/validate-claude-config.py`, `python -m compileall -q .claude/hooks`, `git diff --check`, secret/path scans, and `pip-audit -r requirements.txt` when dependency manifests changed. `security-auditor` must state whether each finding is based on parent-provided evidence or static file inspection. `dependency-audit` evidence is owned by the parent session/`ship` and reviewed by `security-auditor`.

## Output contract for every routed review

Emit the fields in `.claude/rules/evidence-schema.yml`:

- `verdict`: `PASS`, `BLOCK`, or `NEEDS_INFO`.
- `scope_reviewed`.
- `source_of_truth.files` and `source_of_truth.runtime_state`.
- `commands_run` with `PASS`, `FAIL`, `WARNING`, or `NOT_RUN` and reasons.
- `findings.critical`, `findings.important`, and `findings.suggestions`.
- `edge_cases` with coverage status.
- `handoffs`.
- `memory_update.needed` and `memory_update.path`.

## Memory curation convention

Project memory files under `.claude/agent-memory/<agent>/MEMORY.md` should keep durable facts in the first 200 lines because Claude Code loads only the initial portion. Use this section order:

1. `Current operating assumptions` — concise, stable facts needed at startup.
2. `Recent validated learnings` — dated learnings with source/evidence references.
3. `Historical notes` — older context that can be compressed or moved to references.

`docs-memory-curator` audits this convention after memory edits. The validator warns if a memory file exceeds the soft limit without the top summary section.
