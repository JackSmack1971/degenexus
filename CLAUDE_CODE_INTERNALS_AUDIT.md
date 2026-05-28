# Claude Code Internals Audit — Actionable Improvement Plan

**Date:** 2026-05-28
**Scope:** `CLAUDE.md`, `.claude/README.md`, `.claude/settings.json`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/rules/`, `.claude/imports/`, `.claude/output-styles/`, `.claude/hooks/`, and `.claude/agent-memory/`.
**Deliverable constraint:** This file is recommendations-only. No Claude Code internals were modified in this audit refresh.

## Research Baseline

This refresh cross-checked the local setup against the current Claude Code documentation and then verified the repository's actual configuration on disk.

### External references consulted

- Claude Code subagents documentation: <https://code.claude.com/docs/en/sub-agents>
- Claude Code skills documentation: <https://code.claude.com/docs/en/skills>
- Claude Code hooks documentation: <https://code.claude.com/docs/en/hooks>
- Claude Code configuration documentation: <https://code.claude.com/docs/en/configuration>
- Claude Code feature/context-cost overview: <https://code.claude.com/docs/en/features-overview>

### Local evidence commands run

```bash
find .claude -maxdepth 4 -type f -print | sort
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
python - <<'PY'
from pathlib import Path
import yaml
for p in sorted(Path('.claude/agents').glob('*.md')):
    fm = yaml.safe_load(p.read_text().split('---', 2)[1]) or {}
    if fm.get('memory') == 'project':
        d = Path('.claude/agent-memory') / fm['name']
        print(f'{fm["name"]}: MEMORY.md={(d / "MEMORY.md").exists()} memory.md={(d / "memory.md").exists()}')
PY
wc -l CLAUDE.md .claude/README.md .claude/agents/*.md .claude/skills/*/SKILL.md .claude/commands/*.md
```

## Executive Summary

The Claude Code internals are in much better shape than the stale prior audit implied: skill frontmatter parses, missing skill references have been removed, slash commands are project-specific, `.claude/settings.json` exists, and the local config validator passes. The remaining improvements are about **making the system more synergistic and enforceable**, not repairing a broken setup.

Top priorities:

1. **Fix project agent memory loading.** Most agents declare `memory: project`, but the checked-in memory files are named `memory.md` and only exist for a subset of agents. Claude Code documentation says project memory is read from `.claude/agent-memory/<agent-name>/MEMORY.md`, with the first 200 lines or 25KB loaded. This likely means the intended project memory is not being loaded.
2. **Split broad specialist prompts into concise prompts plus skill/reference files.** `security-auditor`, `fdd-investigator`, `code-reviewer`, and `test-engineer` contain long, reusable workflows that would be better expressed as skills or `references/` documents. This reduces subagent startup context and makes multiple agents share the same doctrine.
3. **Make config validation match current Claude Code semantics.** The validator checks YAML and missing skill names, but it does not yet catch lowercase agent memory files, unavailable subagent tools, invalid/unknown frontmatter fields, hook matcher mistakes, or broad permission gaps.
4. **Create explicit synergy contracts between agents and skills.** The agents mostly work in isolation. Add a small machine-readable handoff matrix so `/ship`, `/review`, `/audit`, and domain agents agree on which agent owns each risk surface and what evidence each must return.
5. **Add manual-only flags for expensive or side-effect-prone skills.** Several skills are task workflows, not background knowledge. Claude Code supports `disable-model-invocation: true` for skills that should only run when invoked directly, reducing context noise and accidental activation.

## Current Inventory Snapshot

### Project instruction layer

- `CLAUDE.md` is concise at 99 lines, below the Claude Code guidance to keep project memory under roughly 200 lines and move long workflows to skills.
- `.claude/README.md` provides a useful map of commands, agents, skills, hooks, and validation.
- `.claude/rules/01-security.md`, `.claude/imports/doctrine-summary.md`, and `.claude/output-styles/doctrine-engineer.md` provide supporting doctrine.

### Agents

Current project agents:

- `code-reviewer`
- `docs-memory-curator`
- `fdd-investigator`
- `market-data-integrity-auditor`
- `prompt-injection-auditor`
- `risk-gate-verifier`
- `security-auditor`
- `ship`
- `test-engineer`
- `test-writer` deprecated compatibility alias
- `trade-lifecycle-auditor`

Notable positives:

- Most specialist agents are read-only and set `permissionMode: dontAsk`, which is appropriate for auditors.
- `ship` has a restricted `Agent(...)` allowlist for known child agents.
- `test-engineer` is the only active write-capable testing agent; `test-writer` is deprecated and read-only.
- Domain-specific auditors exist for risk, prompt injection, market data, and trade lifecycle rather than overloading the generic security or review agents.

### Skills

Current project skills:

- `claude-config-audit`
- `code-reviewer`
- `edge-case-audit`
- `forensic-debug`
- `fsv-verify`
- `prompt-safety-review`
- `release-evidence-pack`
- `risk-control-audit`
- `sqlite-sot-verify`

Notable positives:

- Skills use the required `.claude/skills/<skill-name>/SKILL.md` layout.
- Skill descriptions are short enough to avoid the documented 1,536-character description/listing cap.
- There are no stale `agent-skills:*` references in slash commands.
- The current validator reports `claude config validation ok`.

### Commands, settings, and hooks

- Slash commands are compact and DegenExus-specific.
- `.claude/settings.json` denies obvious destructive and secret-reading patterns.
- `PostToolUse` runs `.claude/hooks/validate-claude-config.py` after `Write|Edit|MultiEdit`.
- `SubagentStart` and `SubagentStop` call `.claude/hooks/log-subagent-event.py`.
- Hook scripts compile successfully with `python -m compileall -q .claude/hooks`.

## Findings and Actionable Improvements

### P0 — Rename and normalize project agent memory files

**Finding:** Claude Code's subagent memory documentation describes project memory at `.claude/agent-memory/<agent-name>/MEMORY.md`. The local tree has lowercase `memory.md` for `fdd-investigator`, `security-auditor`, and deprecated `test-writer`; the other `memory: project` agents have no checked-in memory file.

**Why it matters:** The memory feature only helps if Claude Code can discover the expected file. If lowercase files are ignored, the repository has an apparent memory layer that is not actually injected into subagent contexts. This weakens the intended synergy between repeated specialist reviews.

**Recommended target state:**

```text
.claude/agent-memory/
  code-reviewer/MEMORY.md
  docs-memory-curator/MEMORY.md
  fdd-investigator/MEMORY.md
  market-data-integrity-auditor/MEMORY.md
  prompt-injection-auditor/MEMORY.md
  risk-gate-verifier/MEMORY.md
  security-auditor/MEMORY.md
  ship/MEMORY.md
  test-engineer/MEMORY.md
  trade-lifecycle-auditor/MEMORY.md
```

Do **not** create memory for `test-writer` unless it remains a meaningful compatibility agent; otherwise remove or archive the deprecated memory directory after confirming no workflows depend on it.

**Action plan:**

1. Rename existing lowercase memory files to uppercase `MEMORY.md`.
2. Add minimal `MEMORY.md` files for every agent with `memory: project`.
3. Keep each memory file under the documented load limit by making it a curated summary, not a log.
4. Add validator checks:
   - Every agent with `memory: project` must have `.claude/agent-memory/<name>/MEMORY.md`.
   - Lowercase `.claude/agent-memory/**/memory.md` should fail validation.
   - Memory directories for missing or deprecated agents should warn.
5. Add a `Memory Write Criteria` section to every memory file: recurring pattern only, dated source evidence, no secrets, no one-off task notes.

**Acceptance checks:**

```bash
python .claude/hooks/validate-claude-config.py
find .claude/agent-memory -maxdepth 2 -type f | sort
```

### P0 — Expand config validation beyond YAML parsing

**Finding:** `.claude/hooks/validate-claude-config.py` confirms frontmatter parses, skills exist, and stale command references are absent. It does not yet validate many semantics that now matter: project memory naming, whether `tools` includes subagent-unavailable entries, whether hook matchers are valid for each event, whether skill frontmatter uses current hyphenated keys, or whether `permissionMode: bypassPermissions` appears.

**Why it matters:** Claude Code internals can be syntactically valid while semantically inert. The validator should be the one trusted Source of Truth for the setup because `CLAUDE.md` explicitly points to it for Claude setup validation.

**Action plan:**

Add validator rules for:

1. **Agent memory:** enforce `MEMORY.md` for `memory: project`; forbid lowercase `memory.md`.
2. **Agent tool semantics:** flag `Agent` in subagents that are not intended to run as main session agents; the docs say subagents cannot spawn subagents, and `Agent(...)` only matters when an agent runs as the main thread.
3. **Permission modes:** fail on `bypassPermissions`; warn on `acceptEdits` outside known write-capable agents.
4. **Hook event schema:** maintain an allowed event list and warn when a matcher is supplied to events where matchers are ignored, or omitted where the local policy expects one.
5. **Skill frontmatter:** accept and lint current fields such as `disable-model-invocation`, `allowed-tools`, `disallowed-tools`, `model`, `effort`, `context`, `when_to_use`, and `argument-hint`.
6. **Skill/task duplication:** warn when a command and a skill share a name, since docs say skills take precedence over `.claude/commands/` for the same slash name.
7. **README drift:** ensure every agent, skill, hook, and command is listed in `.claude/README.md`.

**Acceptance checks:**

```bash
python .claude/hooks/validate-claude-config.py
python -m pytest tests/ -q -k claude_config  # if/after validator tests are added
```

### P1 — Move reusable agent doctrine into shared skills and references

**Finding:** Several agents contain long reusable workflows directly in their agent prompt files. The largest examples are `security-auditor` at 231 lines, `fdd-investigator` at 152 lines, `code-reviewer` at 130 lines, and `test-engineer` at 125 lines. Claude Code documentation emphasizes context-cost control: project instructions are always loaded, skills load descriptions first and full content only when used, and subagents get isolated context with specified skills.

**Why it matters:** Long specialist prompts make each spawned agent expensive and can cause divergence when two agents need the same doctrine. Shared skills are a better home for repeatable procedure, while the agent prompt should focus on role, tools, scope, output contract, and when to update memory.

**Recommended target state:**

- Keep agent files under roughly 60-90 lines where possible.
- Move detailed checklists into skill `references/` files.
- Preload only the skills a specialist truly needs.

**Concrete refactor map:**

| Current prompt content | Better home | Consuming agents |
| --- | --- | --- |
| OWASP/category security checklist | `.claude/skills/security-review/references/checklist.md` or expand `prompt-safety-review` plus new `dependency-audit` skill | `security-auditor`, `ship` |
| 5-Whys and multi-hypothesis investigation procedure | `.claude/skills/forensic-debug/references/fdd-protocol.md` | `fdd-investigator` |
| Five-axis code-review rubric | `.claude/skills/code-reviewer/references/review-template.md` plus concise SKILL body | `code-reviewer`, `ship` |
| Prove-It and FSV-AAA test writing rules | `.claude/skills/test-regression/SKILL.md` or extend `edge-case-audit`/`fsv-verify` references | `test-engineer`, `ship` |
| Release evidence formatting | `.claude/skills/release-evidence-pack/SKILL.md` | `ship`, `docs-memory-curator` |

**Action plan:**

1. Extract large checklists into `references/` files under the relevant skill directories.
2. Replace the agent body with a concise role contract and references to preloaded skills.
3. Add `when_to_use` to skills where a description alone is too broad.
4. Re-run config validation and manually inspect `/agents` and `/skills` in Claude Code.

### P1 — Add explicit agent-skill synergy contracts

**Finding:** Agents preload skills, but there is no single source mapping risk surface → owning agent → required skills → required evidence. The policy is spread across `CLAUDE.md`, `.claude/README.md`, command prompts, agent frontmatter, and skill text.

**Why it matters:** The most valuable part of this setup is specialist synergy. Without a single handoff matrix, `/ship` and `/review` can under-spawn specialists or receive incompatible outputs.

**Action plan:**

Create one of these lightweight coordination files:

- `.claude/rules/02-agent-synergy.md`, or
- `.claude/imports/agent-synergy-map.md`, or
- `.claude/skills/release-evidence-pack/references/synergy-matrix.md`.

Suggested matrix:

| Trigger | Primary agent | Supporting skill(s) | Required evidence |
| --- | --- | --- | --- |
| `.claude/**`, `CLAUDE.md`, `AGENTS.md` | `docs-memory-curator` | `claude-config-audit`, `release-evidence-pack` | Config validation output, stale reference scan, memory impact |
| Prompt construction, LLM context, cross-agent summaries | `prompt-injection-auditor` | `prompt-safety-review`, `edge-case-audit` | Trust boundary trace, sanitizer evidence, regression coverage |
| Risk gate, execution gate, portfolio exposure | `risk-gate-verifier` | `risk-control-audit`, `fsv-verify`, `edge-case-audit` | PRE/POST source-of-truth reads, rejected bypass paths |
| Trade lifecycle or SQLite state | `trade-lifecycle-auditor` | `sqlite-sot-verify`, `fsv-verify` | Direct SQLite row deltas, restart durability impact |
| Market data, indicators, fallback feeds | `market-data-integrity-auditor` | `edge-case-audit`, `fsv-verify` | NaN/warmup/network degradation cases |
| Bug persists after first fix | `fdd-investigator` | `forensic-debug`, `fsv-verify` | Hypotheses, falsification evidence, root cause |
| Merge readiness | `ship` | `release-evidence-pack`, `claude-config-audit` | GO/NO-GO, command evidence, specialist summary |

Then update `/review`, `/audit`, and `/ship` to reference the same matrix rather than each maintaining separate specialist selection logic.

### P1 — Reclassify task workflows as manual-only skills where appropriate

**Finding:** Claude Code supports `disable-model-invocation: true` for skills that should not be automatically loaded by the model. The local skills currently appear model-invocable by default. Some are reusable doctrine (`fsv-verify`, `edge-case-audit`) and should stay model-invocable; others are explicit workflows that may be better as manual commands.

**Why it matters:** Model-invocable skills add descriptions to the session and can be selected automatically. For expensive, release-gate, or audit workflows, manual invocation can reduce noise and prevent accidental activation.

**Recommended classification:**

| Skill | Suggested invocation mode | Rationale |
| --- | --- | --- |
| `fsv-verify` | Model-invocable | Core doctrine for mutations and source-of-truth proof. |
| `edge-case-audit` | Model-invocable | Broadly useful during design, tests, and reviews. |
| `prompt-safety-review` | Model-invocable | Should trigger automatically on prompt/context work. |
| `risk-control-audit` | Model-invocable | Should trigger automatically on risk/execution work. |
| `sqlite-sot-verify` | Model-invocable | Should trigger automatically on persistence work. |
| `claude-config-audit` | Consider manual-only or agent-preloaded only | Mostly needed for `.claude/**`; `docs-memory-curator` and `/audit` can preload it. |
| `release-evidence-pack` | Manual-only or `/ship`-only | It is a gate workflow, not background knowledge. |
| `forensic-debug` | Model-invocable but with tighter description | Useful on persistent failures; avoid over-triggering on simple bugs. |
| `code-reviewer` | Model-invocable or bundled `/code-review` aware | Keep if it improves project-specific review; avoid conflicting with bundled `/code-review`. |

**Action plan:**

1. Add `disable-model-invocation: true` to release-only skills if they should not auto-trigger.
2. Add `when_to_use` to skills that should auto-trigger narrowly.
3. Add validator output listing all model-invocable skills and their description lengths.
4. Verify `/skills` in Claude Code after changes.

### P1 — Add a project run/verify skill for DegenExus

**Finding:** Claude Code now documents bundled `/run`, `/verify`, and `/run-skill-generator` workflows that can record project-specific launch recipes under `.claude/skills/run-<name>/`. DegenExus has command knowledge in `CLAUDE.md`, but no project run/verify skill.

**Why it matters:** This is a CLI/TUI simulator with a known headless launch command. A project-specific run recipe would reduce rediscovery and make `/verify` more useful after behavioral changes.

**Action plan:**

Create `.claude/skills/run-degenexus/SKILL.md` with a concise recipe:

1. Environment creation and dependency install assumptions.
2. Headless smoke command: `python src/main.py --cycles 1 --no-dashboard --symbols AAPL,SPY`.
3. Agent list command: `python src/main.py --list-agents`.
4. Core checks: `python3 -m compileall -q src/`, targeted pytest, full pytest.
5. Network/yfinance caveat and expected fallback behavior.
6. No real trading guarantee.

If using `/run-skill-generator`, run it once and then curate the generated skill before committing.

### P2 — Tighten hook coverage and hook auditability

**Finding:** The existing hooks are useful but narrow. `PostToolUse` validates config only after write/edit tools; `SubagentStart` and `SubagentStop` log events. Current Claude Code hook docs also support `ConfigChange`, `SessionStart`, `Stop`, `TaskCompleted`, `FileChanged`, prompt hooks, and agent hooks.

**Why it matters:** The current setup can miss drift that happens outside ordinary edits or when config changes are reloaded during a session.

**Action plan:**

1. Add a `ConfigChange` hook that runs `python .claude/hooks/validate-claude-config.py` for `project_settings` and `skills` changes.
2. Add a `SessionStart` hook that prints a short reminder to run or trust the mandatory turn-start ritual if the session was started in this repo.
3. Add a `FileChanged` hook for `.envrc|.env` that warns rather than reads secret content.
4. Consider a `Stop` prompt hook for `/ship` sessions only, asking whether required verification evidence is present before allowing completion.
5. Keep agent hooks experimental; prefer command hooks for production policy because the docs note agent hooks may change.
6. Ensure `.claude/local/` is gitignored if subagent lifecycle logs are written there.

### P2 — Clarify `ship` as main-session orchestrator vs spawned subagent

**Finding:** The `ship` agent has `tools: Agent(...)`, which is valid for restricting subagents when the agent runs as the main thread. Claude Code docs state subagents themselves cannot spawn other subagents, so this tool list has no effect if `ship` is spawned as a normal subagent by another conversation.

**Why it matters:** The repository describes `ship` as a fan-out orchestrator. That behavior depends on invoking it in a mode where the `Agent` tool is actually available.

**Action plan:**

1. In `.claude/commands/ship.md`, explicitly state whether `/ship` should launch `ship` as the main session agent or instruct the current session to perform fan-out.
2. In `.claude/README.md`, document the invocation model:
   - `claude --agent ship` for full orchestrator behavior, or
   - `/ship` as a prompt-level command where the parent agent performs fan-out.
3. Add a validator warning when an agent has `Agent(...)` tools but no documentation explaining it is intended to run as the main thread.
4. Consider renaming `ship` to `ship-coordinator` if it is intended primarily as a main-session agent.

### P2 — Add a dedicated dependency/security audit skill

**Finding:** `security-auditor` mentions CVE and dependency review, but it disallows `Bash`, so it cannot run `pip-audit`. The command table in `CLAUDE.md` includes `pip-audit -r requirements.txt`, but no skill owns dependency audit evidence collection.

**Why it matters:** Security review currently has a split brain: the security agent can reason from manifests, but the parent must remember to run dependency tooling. A small skill would standardize the handoff.

**Action plan:**

Create `.claude/skills/dependency-audit/SKILL.md` with:

- Manual invocation default (`disable-model-invocation: true`) unless security work should trigger it automatically.
- Commands:
  - `pip-audit -r requirements.txt`
  - Optional `python -m pip list --outdated` if dependency freshness matters.
- Output contract:
  - Tool version, command output, Critical/High vulnerabilities, package owner, remediation note.
- Parent-agent handoff:
  - `security-auditor` requests this evidence when it lacks shell access.
  - `/ship` includes the evidence when dependencies changed.

### P2 — Add a prompt-flow inventory for prompt-injection audits

**Finding:** There is a `prompt-injection-auditor` and `prompt-safety-review` skill, but no durable map of prompt construction paths, untrusted inputs, and sanitizers.

**Why it matters:** Prompt-injection safety is a recurring system property. A durable inventory lets the prompt specialist spend time verifying deltas instead of rediscovering data flow every review.

**Action plan:**

Add a reference document such as `.claude/skills/prompt-safety-review/references/prompt-flow-inventory.md` with:

- Prompt construction files/functions.
- Untrusted inputs: market data text, analyst output, logs, memory, prior-agent reasoning, CLI args, DB text.
- Sanitizers and boundaries.
- Tests that cover prompt-injection scenarios.
- Known false positives and unresolved gaps.

Then preload this skill for `prompt-injection-auditor` and cite the inventory from `.claude/README.md`.

### P2 — Add outcome-oriented slash command outputs

**Finding:** Slash commands are concise, but several do not require the final answer to include exact evidence, owner, and next step. `/ship` is strong; `/audit`, `/review`, `/test`, and `/plan` can borrow its output discipline.

**Why it matters:** Consistent output contracts make subagent results easier to combine. This is especially important when multiple specialists participate.

**Action plan:**

Update commands to require final sections:

- **Scope reviewed**
- **Source of Truth used**
- **Specialists/skills invoked**
- **Evidence commands and exact results**
- **Findings by severity**
- **At least three edge cases considered**
- **Memory update needed? yes/no + path**
- **Next action owner**

### P3 — Add tests for Claude internals validators and hooks

**Finding:** The hook scripts are executable Python, but they appear to be validated only by compile checks and direct execution. There are no obvious unit tests dedicated to `.claude/hooks/validate-claude-config.py` or `.claude/hooks/log-subagent-event.py`.

**Why it matters:** Once the validator becomes the Source of Truth for Claude internals, it needs regression tests. Otherwise future changes can silently weaken checks.

**Action plan:**

1. Add `tests/test_claude_config_validator.py` with temporary `.claude` fixtures or helper functions that accept a root path.
2. Test invalid YAML frontmatter, missing skills, lowercase memory files, stale `agent-skills:*`, command/skill name collisions, and forbidden permission modes.
3. Add `tests/test_subagent_event_logger.py` with a temporary log path and mocked git output.
4. Keep hook scripts dependency-light so they work before the project environment is fully installed.

### P3 — Document plugin and bundled-skill boundaries

**Finding:** The setup previously had stale plugin-style references. The current setup removes them, but the README could be clearer about which capabilities are project-local versus bundled Claude Code behavior.

**Why it matters:** Claude Code now includes bundled prompt-based skills such as `/code-review`, `/batch`, `/debug`, `/loop`, and `/claude-api`, and skills can override command names. Without a boundary document, future contributors may accidentally reintroduce plugin-only names or duplicate bundled skills.

**Action plan:**

Add a section to `.claude/README.md`:

- **Project-local:** all files in `.claude/agents`, `.claude/skills`, `.claude/commands`, `.claude/hooks`, `.claude/settings.json`.
- **Bundled Claude Code:** `/code-review`, `/batch`, `/debug`, `/loop`, `/claude-api`, `/run`, `/verify` when available.
- **External/plugin:** any `plugin-name:skill-name` references must list plugin source, version, and verification command.
- **Collision policy:** project skills should not reuse bundled names unless intentionally overriding behavior.

## Suggested Implementation Order

1. **Memory correctness PR:** rename/add `MEMORY.md` files and update validator checks.
2. **Validator hardening PR:** add semantic checks and tests for hooks/config.
3. **Synergy matrix PR:** add the agent-skill handoff matrix and point `/ship`, `/review`, `/audit`, and `CLAUDE.md` to it.
4. **Prompt diet PR:** move large checklists from long agent prompts into skills/references.
5. **Run/verify PR:** add `run-degenexus` and optional dependency-audit skill.
6. **Hook expansion PR:** add `ConfigChange`, selected `SessionStart`, and `.env` warning hooks.

## Definition of Done for the Next Claude Internals Pass

A future pass should be considered complete when all of these are true:

- `python .claude/hooks/validate-claude-config.py` passes and enforces memory naming, skill existence, hook schema, and high-risk permission rules.
- Every `memory: project` agent has a curated `.claude/agent-memory/<agent>/MEMORY.md` file.
- `/ship` documentation clearly states how the orchestrator can actually fan out to specialists.
- Reusable checklists live in skills or skill references, not duplicated in long agent prompts.
- Commands share a consistent evidence-first output contract.
- Claude internals hook scripts have unit coverage or fixture-based tests.
- `.claude/README.md` distinguishes project-local, bundled, and plugin-provided capabilities.

## Single-PR Implementation Map — 2026-05-28

This section maps every finding above to the concrete project-local change made in the single implementation PR so a downstream reviewer can verify readiness without re-deriving the audit.

| Audit item | Implemented resolution | Review evidence |
| --- | --- | --- |
| Fix project agent memory loading | Added or renamed every `memory: project` agent file to `.claude/agent-memory/<agent>/MEMORY.md` and hardened the validator to reject missing or lowercase-only memory files. | `python .claude/hooks/validate-claude-config.py`; inspect `.claude/agent-memory/*/MEMORY.md`. |
| Split broad specialist prompts into concise prompts plus skills/references | Reduced `security-auditor`, `fdd-investigator`, `code-reviewer`, and `test-engineer` prompts to role/output contracts and moved reusable procedure into `security-review`, `forensic-debug/references/fdd-protocol.md`, `code-reviewer/references/review-template.md`, and `test-regression`. | `wc -l .claude/agents/*.md`; inspect referenced skills. |
| Add explicit agent-skill synergy contracts | Added `.claude/rules/02-agent-synergy.md` and updated `/audit`, `/review`, `/ship`, `/plan`, README, and release evidence references to use it as the routing source of truth. | Inspect `.claude/rules/02-agent-synergy.md` and command prompts. |
| Reclassify task workflows as manual-only skills where appropriate | Marked release/config/run/dependency gate skills with `disable-model-invocation: true` and added targeted `when_to_use` metadata for model-invocable skills. | Validator prints model-invocable skill inventory. |
| Add project run/verify skill | Added `.claude/skills/run-degenexus/SKILL.md` with environment setup, smoke commands, verification commands, yfinance caveat, and no-real-trading guarantee. | Inspect the skill and README skill matrix. |
| Tighten hook coverage and auditability | Added `ConfigChange`, `SessionStart`, and `FileChanged` hook wiring plus `session-start-reminder.py` and `warn-env-file-changed.py`; preserved subagent lifecycle logging and `.claude/local/` gitignore. | `python -m compileall -q .claude/hooks`; inspect `.claude/settings.json`. |
| Clarify `ship` invocation model | Updated `/ship` and README to distinguish `claude --agent ship` main-session fan-out from `/ship` parent-session fan-out. Validator warns if `Agent(...)` tools lack this documentation. | Inspect `.claude/commands/ship.md` and `.claude/README.md`. |
| Add dependency/security audit skill | Added manual-only `.claude/skills/dependency-audit/SKILL.md` and wired `security-auditor`, `/ship`, and README to request or collect dependency evidence. | Inspect dependency-audit skill and security auditor prompt. |
| Add prompt-flow inventory | Added `.claude/skills/prompt-safety-review/references/prompt-flow-inventory.md` and README guidance for prompt-injection reviews. | Inspect inventory and prompt-safety README section. |
| Add outcome-oriented slash command outputs | Updated `/audit`, `/review`, `/ship`, `/test`, and `/plan` to require scope, SoT, specialists, exact evidence, severity, edge cases, memory status, and owner. | Inspect command prompts. |
| Add validator and hook tests | Added `tests/test_claude_config_validator.py` and `tests/test_subagent_event_logger.py` for config semantics and lifecycle logging. | `python -m pytest tests/test_claude_config_validator.py tests/test_subagent_event_logger.py -q`. |
| Document plugin and bundled-skill boundaries | Added README capability boundaries covering project-local, bundled Claude Code, external/plugin references, and collision policy. Validator enforces README inventory drift. | Inspect `.claude/README.md`; run validator. |

### Single-PR Definition of Done

The Claude internals pass is ready for review when these checks pass in this branch:

```bash
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
python -m pytest tests/test_claude_config_validator.py tests/test_subagent_event_logger.py -q
```
