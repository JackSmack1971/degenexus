# Claude Code Internals Map

This directory is a first-class subsystem for DegenExus agent workflows. Validate it with:

```bash
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
```

Inside Claude Code, also run `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status` after significant configuration changes. Record those checks with `.claude/skills/claude-config-audit/references/live-smoke-template.md` when `.claude/**`, `CLAUDE.md`, or `AGENTS.md` changed.

## Capability Boundaries

- **Project-local:** files in `.claude/agents`, `.claude/skills`, `.claude/commands`, `.claude/rules`, `.claude/imports`, `.claude/output-styles`, `.claude/hooks`, `.claude/agent-memory`, and `.claude/settings.json`.
- **Bundled Claude Code:** `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, and `/verify` when available in the installed Claude Code version.
- **External/plugin:** any `plugin-name:skill-name` or `agent-skills:*` reference must document plugin source, version, and verification command before use.
- **Collision policy:** every user-facing command in `.claude/commands/` is a compatibility shim to its same-name canonical skill; the skill is canonical and the command only points to it.

## Directory Purpose

| Path | Purpose |
| --- | --- |
| `.claude/agents/` | Project subagents checked into source control for team-wide specialist behavior. |
| `.claude/skills/` | Reusable on-demand workflows loaded by agents or commands. |
| `.claude/commands/` | Compatibility slash-command shims that point to canonical skills and verification evidence. |
| `.claude/rules/` | Supplemental durable rules, including `synergy-contract.yml`, `evidence-schema.yml`, `settings-policy-waivers.yml`, security, and the human-readable agent-skill synergy map. |
| `.claude/imports/` | Shared doctrine snippets imported into Claude workflows. |
| `.claude/output-styles/` | Output style definitions. |
| `.claude/agent-memory/` | Project-scoped specialist memory. Files must be `.claude/agent-memory/<agent>/MEMORY.md`. |
| `.claude/hooks/` | Automation scripts for config validation, protected-file blocking, subagent/instruction audit logging, session/CWD reminders, evidence validation, and secret-file warnings. |
| `.claude/local/` | Gitignored local hook output. |

<!-- BEGIN GENERATED CLAUDE INVENTORY -->

### Generated Claude Inventory

#### Agents

| Agent | Permission mode | Write-capable | Preloaded skills | Memory |
| --- | --- | --- | --- | --- |
| `code-reviewer` | `dontAsk` | No | `code-reviewer` | Project |
| `docs-memory-curator` | `dontAsk` | No | `claude-config-audit`, `release-evidence-pack` | Project |
| `fdd-investigator` | `dontAsk` | No | `forensic-debug`, `fsv-verify` | Project |
| `market-data-integrity-auditor` | `dontAsk` | No | `edge-case-audit`, `fsv-verify` | Project |
| `prompt-injection-auditor` | `dontAsk` | No | `prompt-safety-review`, `edge-case-audit` | Project |
| `risk-gate-verifier` | `dontAsk` | No | `risk-control-audit`, `edge-case-audit`, `fsv-verify` | Project |
| `security-auditor` | `dontAsk` | No | `security-review`, `prompt-safety-review`, `claude-config-audit` | Project |
| `ship` | `dontAsk` | No | `claude-config-audit`, `release-evidence-pack` | Project |
| `test-engineer` | `acceptEdits` | Yes | `test-regression`, `edge-case-audit`, `fsv-verify` | Project |
| `test-writer` | `dontAsk` | No | — | None |
| `trade-lifecycle-auditor` | `dontAsk` | No | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` | Project |

#### Skills

| Skill | Invocation mode | Owner agents |
| --- | --- | --- |
| `audit` | Manual-only | parent session |
| `build` | Manual-only | parent session |
| `claude-config-audit` | Manual-only | `docs-memory-curator`, `security-auditor`, `ship` |
| `code-reviewer` | Model-invocable | `code-reviewer` |
| `code-simplify` | Manual-only | parent session |
| `dependency-audit` | Manual-only | parent session |
| `edge-case-audit` | Model-invocable | `market-data-integrity-auditor`, `prompt-injection-auditor`, `risk-gate-verifier`, `test-engineer`, `trade-lifecycle-auditor` |
| `forensic-debug` | Model-invocable | `fdd-investigator` |
| `fsv-verify` | Model-invocable | `fdd-investigator`, `market-data-integrity-auditor`, `risk-gate-verifier`, `test-engineer`, `trade-lifecycle-auditor` |
| `fsv-verify-deep` | Manual-only | parent session |
| `plan` | Manual-only | parent session |
| `prompt-safety-review` | Model-invocable | `prompt-injection-auditor`, `security-auditor` |
| `release-evidence-pack` | Manual-only | `docs-memory-curator`, `ship` |
| `review` | Manual-only | parent session |
| `risk-control-audit` | Model-invocable | `risk-gate-verifier` |
| `run-degenexus` | Manual-only | parent session |
| `security-review` | Model-invocable | `security-auditor` |
| `ship` | Manual-only | parent session |
| `spec` | Manual-only | parent session |
| `sqlite-sot-verify` | Model-invocable | `trade-lifecycle-auditor` |
| `test` | Manual-only | parent session |
| `test-regression` | Model-invocable | `test-engineer` |

#### Commands

| Command | Canonical source |
| --- | --- |
| `/audit` | `.claude/skills/audit/SKILL.md` |
| `/build` | `.claude/skills/build/SKILL.md` |
| `/code-simplify` | `.claude/skills/code-simplify/SKILL.md` |
| `/plan` | `.claude/skills/plan/SKILL.md` |
| `/review` | `.claude/skills/review/SKILL.md` |
| `/ship` | `.claude/skills/ship/SKILL.md` |
| `/spec` | `.claude/skills/spec/SKILL.md` |
| `/test` | `.claude/skills/test/SKILL.md` |

#### Hooks

| Hook script | Events |
| --- | --- |
| `cwd-changed-reminder.py` | `CwdChanged` |
| `log-instructions-loaded.py` | `InstructionsLoaded` |
| `log-subagent-event.py` | `SubagentStart`, `SubagentStop` |
| `protect-sensitive-files.py` | `PreToolUse` |
| `session-start-reminder.py` | `SessionStart` |
| `validate-claude-config.py` | `ConfigChange`, `PostToolUse` |
| `validate-evidence-payload.py` | Not registered |
| `warn-env-file-changed.py` | `FileChanged` |

#### Memories

| Agent memory | Status |
| --- | --- |
| `code-reviewer` | Present |
| `docs-memory-curator` | Present |
| `fdd-investigator` | Present |
| `market-data-integrity-auditor` | Present |
| `prompt-injection-auditor` | Present |
| `risk-gate-verifier` | Present |
| `security-auditor` | Present |
| `ship` | Present |
| `test-engineer` | Present |
| `test-writer` | Present |
| `trade-lifecycle-auditor` | Present |

<!-- END GENERATED CLAUDE INVENTORY -->


## Agent Matrix

| Agent | Writes? | Default use | Preloaded skills |
| --- | --- | --- | --- |
| `ship` | No direct edits | Main-session pre-merge orchestration and GO/NO-GO evidence | `claude-config-audit`, `release-evidence-pack` |
| `code-reviewer` | No | Five-dimension code review | `code-reviewer` |
| `security-auditor` | No | Security evidence consumer for dependencies, prompt safety, auth/secrets, and protected-file policy | `security-review`, `prompt-safety-review`, `claude-config-audit` |
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
| `audit` | Manual slash skill | Claude internals audit workflow | parent session, `docs-memory-curator` |
| `build` | Manual slash skill | Incremental implementation with tests and FSV evidence | parent session, `test-engineer` |
| `claude-config-audit` | Manual or preloaded | `.claude/**` or Claude setup changes | `ship`, `docs-memory-curator` |
| `code-reviewer` | Model-invocable | Five-dimension review | `code-reviewer` |
| `code-simplify` | Manual slash skill | Behavior-preserving simplification | parent session, `code-reviewer` |
| `dependency-audit` | Manual-only | Dependency scan evidence | parent session, `ship`, `security-auditor` handoff |
| `edge-case-audit` | Model-invocable | Safety-critical boundary/failure/resilience analysis | `test-engineer`, domain auditors |
| `forensic-debug` | Model-invocable, narrow trigger | Root-cause reconstruction | `fdd-investigator` |
| `fsv-verify` | Model-invocable, slim doctrine | Any mutation or SoT proof | `test-engineer`, `fdd-investigator`, domain auditors |
| `fsv-verify-deep` | Manual-only | High-risk or disputed SoT verification | parent session, domain auditors by escalation |
| `plan` | Manual slash skill | Read-only task planning and specialist map | parent session |
| `prompt-safety-review` | Model-invocable | Prompt-safety and trust-boundary review | `security-auditor`, `prompt-injection-auditor` |
| `release-evidence-pack` | Manual-only or `/ship`-only | PR/ship evidence assembly | `ship`, `docs-memory-curator` |
| `review` | Manual slash skill | Contract-driven five-axis review workflow | parent session, `code-reviewer` |
| `risk-control-audit` | Model-invocable | Trading risk-control review | `risk-gate-verifier` |
| `run-degenexus` | Manual-only | Project run and verify recipe | parent session |
| `security-review` | Model-invocable | Security checklist and dependency handoff | `security-auditor` |
| `ship` | Manual slash skill | Pre-merge GO/NO-GO gate | parent session, `ship` |
| `spec` | Manual slash skill | Spec-driven development setup | parent session |
| `sqlite-sot-verify` | Model-invocable | SQLite state verification | `trade-lifecycle-auditor` |
| `test` | Manual slash skill | Pytest/Prove-It workflow | parent session, `test-engineer` |
| `test-regression` | Model-invocable | Prove-It and FSV-AAA pytest authoring | `test-engineer` |

## Command Matrix

| Command | Primary agents/skills | Required evidence |
| --- | --- | --- |
| `/audit` | Compatibility shim to `audit` skill | Config validation, hook compile output, memory naming, README inventory, schema fields. |
| `/build` | Compatibility shim to `build` skill | Failing test, passing test, SoT delta, compile for runtime changes. |
| `/code-simplify` | Compatibility shim to `code-simplify` skill | Behavior-preserving tests and SoT comparison. |
| `/plan` | Compatibility shim to `plan` skill | Acceptance criteria, verification steps, edge cases, specialist map. |
| `/review` | Compatibility shim to `review` skill | File-specific findings, specialist routing, schema fields. |
| `/ship` | Compatibility shim to `ship` skill | GO/NO-GO, command evidence, specialist findings, edge cases, memory status. |
| `/spec` | Compatibility shim to `spec` skill | Spec, boundaries, FSV evidence expectations. |
| `/test` | Compatibility shim to `test` skill | Pytest evidence, FSV-AAA assertions, mocked external dependencies, schema fields. |

## Hook Inventory

| Hook script | Event(s) | Purpose |
| --- | --- | --- |
| `protect-sensitive-files.py` | `PreToolUse` | Block reads/writes/edits/Bash paths targeting `.env*`, `secrets/**`, credential keys, or SQLite runtime files before tool execution. |
| `validate-claude-config.py` | `PostToolUse`, `ConfigChange` | Validate frontmatter, skills, memory naming, protected-file policy, evidence schema, synergy contract, command shims, settings schema, hooks, read-only tools, generated inventory, and README drift. |
| `log-subagent-event.py` | `SubagentStart`, `SubagentStop` | Append local JSONL lifecycle evidence to `.claude/local/subagent-events.jsonl`. |
| `log-instructions-loaded.py` | `InstructionsLoaded` | Append redacted instruction-load summaries to `.claude/local/instructions-loaded.jsonl`. |
| `cwd-changed-reminder.py` | `CwdChanged` | Remind sessions that hook commands should stay rooted at `CLAUDE_PROJECT_DIR`. |
| `session-start-reminder.py` | `SessionStart` | Print a short project ritual and routing reminder. |
| `warn-env-file-changed.py` | `FileChanged` | Warn when `.env` or `.envrc` files change without reading secret content. |
| `validate-evidence-payload.py` | Manual `/ship` helper | Validate JSON/YAML/Markdown specialist evidence against `.claude/rules/evidence-schema.yml`. |

## Rule Inventory

- `01-security.md` — durable security and prompt-injection policy.
- `02-agent-synergy.md` — human-readable routing map, test-agent ownership, security-auditor command boundary, and memory convention.
- `synergy-contract.yml` — machine-readable risk-surface routing contract.
- `evidence-schema.yml` — schema-checkable specialist and release output contract.
- `settings-policy-waivers.yml` — explicit sandbox/network waiver record for settings surfaces.

## Write-capable Exception Register

Only `test-engineer` may grant `Write`, `Edit`, or `MultiEdit`, and it must use `permissionMode: acceptEdits`. All other agents are read-only or orchestration-only and must not grant write tools; `ship` may orchestrate specialists but has `Write`, `Edit`, and `MultiEdit` in `disallowedTools`. The validator constant `KNOWN_WRITE_CAPABLE_AGENTS` must stay in sync with this register.

## Skill Context Cost

Keep model-invocable skills small because invoked skills can remain in context after use and may be reattached after compaction. `fsv-verify` is the slim always-available doctrine skill; load `fsv-verify-deep` only for high-risk or disputed evidence. `edge-case-audit` should be used for safety-critical boundaries, resilience, and coupled failure modes rather than generic brainstorming. Heavy checklists belong in `references/` and should be loaded only on demand.

## Agent-Skill Synergy

The machine-readable routing source of truth is `.claude/rules/synergy-contract.yml`; the human-readable companion is `.claude/rules/02-agent-synergy.md`. All command shims and specialists must cite those files rather than maintaining divergent fan-out logic.

## Evidence Schema

Every routed specialist output and release evidence pack must emit `.claude/rules/evidence-schema.yml` fields: `verdict`, `scope_reviewed`, `source_of_truth`, `commands_run`, `findings`, `edge_cases`, `handoffs`, and `memory_update`.

## Memory Curation

Agent memories are loaded only from the initial portion of `.claude/agent-memory/<agent>/MEMORY.md`. Keep the first 200 lines concise and ordered as `Current operating assumptions`, `Recent validated learnings`, then `Historical notes`.

## Prompt-Flow Inventory

Prompt-injection reviews should start from `.claude/skills/prompt-safety-review/references/prompt-flow-inventory.md`, then verify the exact touched files and tests for the current change.

## Naming Rules

- Agents use noun-role names such as `security-auditor`.
- Skills use workflow names such as `prompt-safety-review`; user-facing slash workflows are intentional manual workflow-skill exceptions with command shims.
- Commands use user action names such as `/ship`.
- Avoid stale `agent-skills:*` references unless a plugin dependency is documented and verified.
