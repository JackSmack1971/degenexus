# Claude Code Internals Map

This directory is a first-class subsystem for DegenExus agent workflows. Validate it with:

```bash
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
```

Inside Claude Code, also run `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status` after significant configuration changes.

## Directory Purpose

| Path | Purpose |
| --- | --- |
| `.claude/agents/` | Project subagents checked into source control for team-wide specialist behavior. |
| `.claude/skills/` | Reusable on-demand workflows loaded by agents or commands. |
| `.claude/commands/` | Slash-command playbooks that invoke local agents/skills and verification evidence. |
| `.claude/rules/` | Supplemental durable rules, especially security and trust-boundary policy. |
| `.claude/imports/` | Shared doctrine snippets imported into Claude workflows. |
| `.claude/output-styles/` | Output style definitions. |
| `.claude/agent-memory/` | Project-scoped specialist memory with strict write criteria. |
| `.claude/hooks/` | Automation scripts for config validation and subagent audit logging. |
| `.claude/local/` | Gitignored local hook output. |

## Agent Matrix

| Agent | Writes? | Default use | Preloaded skills |
| --- | --- | --- | --- |
| `ship` | No direct edits | Pre-merge orchestration and GO/NO-GO evidence | `claude-config-audit`, `release-evidence-pack` |
| `code-reviewer` | No | Five-dimension code review | `code-reviewer` |
| `security-auditor` | No | Security, dependency, prompt-safety, auth/secrets review | `prompt-safety-review`, `claude-config-audit` |
| `test-engineer` | Yes | Single authoritative pytest author and coverage analyst | `edge-case-audit`, `fsv-verify` |
| `test-writer` | No | Deprecated alias; redirect to `test-engineer` | none |
| `fdd-investigator` | No | Read-only root-cause analysis for persistent failures | `forensic-debug`, `fsv-verify` |
| `risk-gate-verifier` | No | Risk/execution/portfolio gate audit | `risk-control-audit`, `edge-case-audit`, `fsv-verify` |
| `prompt-injection-auditor` | No | Prompt construction and cross-agent text-flow audit | `prompt-safety-review`, `edge-case-audit` |
| `trade-lifecycle-auditor` | No | Trade state machine and SQLite SoT audit | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` |
| `market-data-integrity-auditor` | No | yfinance/OHLCV/indicator/fallback audit | `edge-case-audit`, `fsv-verify` |
| `docs-memory-curator` | No | Docs, memory, issues, PR evidence consistency | `claude-config-audit`, `release-evidence-pack` |

## Skill Matrix

| Skill | Trigger | Owner agents | Status |
| --- | --- | --- | --- |
| `claude-config-audit` | `.claude/**` or Claude setup changes | `ship`, `docs-memory-curator` | active |
| `code-reviewer` | Five-dimension review | `code-reviewer` | active |
| `edge-case-audit` | Boundary/failure/resilience analysis | `test-engineer`, domain auditors | active |
| `forensic-debug` | Root-cause reconstruction | `fdd-investigator` | active |
| `fsv-verify` | Any mutation or SoT proof | `test-engineer`, `fdd-investigator`, domain auditors | active |
| `prompt-safety-review` | Prompt-safety and trust-boundary review | `security-auditor`, `prompt-injection-auditor` | active |
| `risk-control-audit` | Trading risk-control review | `risk-gate-verifier` | active |
| `release-evidence-pack` | PR/ship evidence assembly | `ship`, `docs-memory-curator` | active |
| `sqlite-sot-verify` | SQLite state verification | `trade-lifecycle-auditor` | active |

## Command Matrix

| Command | Primary agents/skills | Required evidence |
| --- | --- | --- |
| `/audit` | `claude-config-audit`, `release-evidence-pack` | Config validation and hook compile output. |
| `/build` | `test-engineer`, `edge-case-audit`, `fsv-verify` | Failing test, passing test, SoT delta, compile for runtime changes. |
| `/code-simplify` | `code-reviewer`, `fsv-verify` | Behavior-preserving tests and SoT comparison. |
| `/plan` | Read-only planning | Acceptance criteria, verification steps, edge cases, specialist map. |
| `/review` | `code-reviewer` plus domain specialists | File-specific findings and recommendations. |
| `/ship` | `ship` orchestrator | GO/NO-GO, command evidence, specialist findings, edge cases, memory status. |
| `/spec` | `edge-case-audit` | Spec, boundaries, FSV evidence expectations. |
| `/test` | `test-engineer` | Pytest evidence, FSV-AAA assertions, mocked external dependencies. |

## Naming Rules

- Agents use noun-role names such as `security-auditor`.
- Skills use workflow names such as `prompt-safety-review`.
- Commands use user action names such as `/ship`.
- Avoid stale `agent-skills:*` references unless a plugin dependency is documented and verified.
