# Claude Code Internals Map

This directory is a first-class subsystem for DegenExus agent workflows. Validate it with:

```bash
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
```

Inside Claude Code, also run `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status` after significant configuration changes.

## Capability Boundaries

- **Project-local:** files in `.claude/agents`, `.claude/skills`, `.claude/commands`, `.claude/rules`, `.claude/imports`, `.claude/output-styles`, `.claude/hooks`, `.claude/agent-memory`, and `.claude/settings.json`.
- **Bundled Claude Code:** `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, and `/verify` when available in the installed Claude Code version.
- **External/plugin:** any `plugin-name:skill-name` or `agent-skills:*` reference must document plugin source, version, and verification command before use.
- **Collision policy:** project skills and commands should not reuse bundled names unless the override is intentional and documented. Skills with the same slash name can take precedence over `.claude/commands/`.

## Directory Purpose

| Path | Purpose |
| --- | --- |
| `.claude/agents/` | Project subagents checked into source control for team-wide specialist behavior. |
| `.claude/skills/` | Reusable on-demand workflows loaded by agents or commands. |
| `.claude/commands/` | Slash-command playbooks that invoke local agents/skills and verification evidence. |
| `.claude/rules/` | Supplemental durable rules, including security and the agent-skill synergy map. |
| `.claude/imports/` | Shared doctrine snippets imported into Claude workflows. |
| `.claude/output-styles/` | Output style definitions. |
| `.claude/agent-memory/` | Project-scoped specialist memory. Files must be `.claude/agent-memory/<agent>/MEMORY.md`. |
| `.claude/hooks/` | Automation scripts for config validation, subagent audit logging, session reminders, and secret-file warnings. |
| `.claude/local/` | Gitignored local hook output. |

## Agent Matrix

| Agent | Writes? | Default use | Preloaded skills |
| --- | --- | --- | --- |
| `ship` | No direct edits | Main-session pre-merge orchestration and GO/NO-GO evidence | `claude-config-audit`, `release-evidence-pack` |
| `code-reviewer` | No | Five-dimension code review | `code-reviewer` |
| `security-auditor` | No | Security, dependency handoff, prompt-safety, auth/secrets review | `security-review`, `prompt-safety-review`, `claude-config-audit` |
| `test-engineer` | Yes | Single authoritative pytest author and coverage analyst | `test-regression`, `edge-case-audit`, `fsv-verify` |
| `test-writer` | No | Deprecated alias; redirect to `test-engineer` | none |
| `fdd-investigator` | No | Read-only root-cause analysis for persistent failures | `forensic-debug`, `fsv-verify` |
| `risk-gate-verifier` | No | Risk/execution/portfolio gate audit | `risk-control-audit`, `edge-case-audit`, `fsv-verify` |
| `prompt-injection-auditor` | No | Prompt construction and cross-agent text-flow audit | `prompt-safety-review`, `edge-case-audit` |
| `trade-lifecycle-auditor` | No | Trade state machine and SQLite SoT audit | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` |
| `market-data-integrity-auditor` | No | yfinance/OHLCV/indicator/fallback audit | `edge-case-audit`, `fsv-verify` |
| `docs-memory-curator` | No | Docs, memory, issues, PR evidence consistency | `claude-config-audit`, `release-evidence-pack` |

## Main-Session Orchestration

`ship` has an `Agent(...)` tool allowlist. That allowlist only enables fan-out when `ship` runs as the main-session agent, for example with `claude --agent ship`. If `/ship` is invoked from another session, the parent session must fan out to specialists directly because a spawned subagent cannot spawn more subagents.

## Skill Matrix

| Skill | Invocation mode | Trigger | Owner agents |
| --- | --- | --- | --- |
| `claude-config-audit` | Manual or preloaded | `.claude/**` or Claude setup changes | `ship`, `docs-memory-curator` |
| `code-reviewer` | Model-invocable | Five-dimension review | `code-reviewer` |
| `dependency-audit` | Manual-only | Dependency scan evidence | parent session, `ship`, `security-auditor` handoff |
| `edge-case-audit` | Model-invocable | Boundary/failure/resilience analysis | `test-engineer`, domain auditors |
| `forensic-debug` | Model-invocable, narrow trigger | Root-cause reconstruction | `fdd-investigator` |
| `fsv-verify` | Model-invocable | Any mutation or SoT proof | `test-engineer`, `fdd-investigator`, domain auditors |
| `prompt-safety-review` | Model-invocable | Prompt-safety and trust-boundary review | `security-auditor`, `prompt-injection-auditor` |
| `release-evidence-pack` | Manual-only or `/ship`-only | PR/ship evidence assembly | `ship`, `docs-memory-curator` |
| `risk-control-audit` | Model-invocable | Trading risk-control review | `risk-gate-verifier` |
| `run-degenexus` | Manual-only | Project run and verify recipe | parent session |
| `security-review` | Model-invocable | Security checklist and dependency handoff | `security-auditor` |
| `sqlite-sot-verify` | Model-invocable | SQLite state verification | `trade-lifecycle-auditor` |
| `test-regression` | Model-invocable | Prove-It and FSV-AAA pytest authoring | `test-engineer` |

## Command Matrix

| Command | Primary agents/skills | Required evidence |
| --- | --- | --- |
| `/audit` | `claude-config-audit`, `release-evidence-pack` | Config validation, hook compile output, memory naming, README inventory. |
| `/build` | `test-engineer`, `edge-case-audit`, `fsv-verify` | Failing test, passing test, SoT delta, compile for runtime changes. |
| `/code-simplify` | `code-reviewer`, `fsv-verify` | Behavior-preserving tests and SoT comparison. |
| `/plan` | Read-only planning plus synergy map | Acceptance criteria, verification steps, edge cases, specialist map. |
| `/review` | `code-reviewer` plus domain specialists per synergy map | File-specific findings and recommendations. |
| `/ship` | `ship` main-session orchestrator or parent-session fan-out | GO/NO-GO, command evidence, specialist findings, edge cases, memory status. |
| `/spec` | `edge-case-audit` | Spec, boundaries, FSV evidence expectations. |
| `/test` | `test-engineer`, `test-regression` | Pytest evidence, FSV-AAA assertions, mocked external dependencies. |

## Hook Inventory

| Hook script | Event(s) | Purpose |
| --- | --- | --- |
| `validate-claude-config.py` | `PostToolUse`, `ConfigChange` | Validate frontmatter, skills, memory naming, permissions, hook schema, command collisions, and README drift. |
| `log-subagent-event.py` | `SubagentStart`, `SubagentStop` | Append local JSONL lifecycle evidence to `.claude/local/subagent-events.jsonl`. |
| `session-start-reminder.py` | `SessionStart` | Print a short project ritual and routing reminder. |
| `warn-env-file-changed.py` | `FileChanged` | Warn when `.env` or `.envrc` files change without reading secret content. |

## Agent-Skill Synergy

The routing source of truth is `.claude/rules/02-agent-synergy.md`. `/audit`, `/review`, `/ship`, and specialists must cite that file rather than maintaining divergent fan-out logic.

## Prompt-Flow Inventory

Prompt-injection reviews should start from `.claude/skills/prompt-safety-review/references/prompt-flow-inventory.md`, then verify the exact touched files and tests for the current change.

## Naming Rules

- Agents use noun-role names such as `security-auditor`.
- Skills use workflow names such as `prompt-safety-review`.
- Commands use user action names such as `/ship`.
- Avoid stale `agent-skills:*` references unless a plugin dependency is documented and verified.
