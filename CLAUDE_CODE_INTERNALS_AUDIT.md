# Claude Code Internals Audit — Actionable Improvement Plan

**Date:** 2026-05-28  
**Scope:** `CLAUDE.md`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/rules/`, `.claude/imports/`, `.claude/output-styles/`, and `.claude/agent-memory/`.  
**Constraint honored:** This audit creates recommendations only and does **not** modify the Claude setup files themselves.

## Executive Summary

DegenExus has a strong Claude Code foundation: a project-level doctrine, task-specialized agents, reusable skills, command wrappers, security rules, and agent memory folders. The main opportunity is to make the setup more internally consistent and more aligned with current Claude Code behavior: subagents are selected by `description`, scoped by frontmatter, can preload named skills, and may use project or user memory; skills are on-demand context modules with `SKILL.md` frontmatter; settings and hooks provide enforceable automation; and `/context`, `/agents`, `/skills`, `/hooks`, and `/doctor` are the operational checks for what actually loaded.

The highest-value improvements are:

1. **Fix invalid skill frontmatter** so Claude Code can discover and invoke all intended skills.
2. **Align agent-to-skill references** by either adding missing skills or removing stale references.
3. **Reduce duplicated / contradictory roles** between `code-reviewer`, `test-engineer`, `test-writer`, and `/ship`.
4. **Add Claude Code settings and hooks** to enforce doctrine-critical checks automatically instead of relying only on prose.
5. **Shorten and stratify `CLAUDE.md`** so always-loaded instructions stay high-signal while long playbooks move into skills, commands, or imports.
6. **Introduce synergy-oriented agents and skills** that match DegenExus domains: risk-gate verifier, prompt-injection auditor, trade-lifecycle auditor, market-data integrity auditor, and documentation/issue closer.

## Research Baseline Used

The recommendations below are grounded in current Claude Code documentation and Anthropic guidance:

- Project subagents live in `.claude/agents/`, are Markdown files with YAML frontmatter, and should have clear `description` fields because Claude uses those descriptions for automatic delegation. The docs state that project subagents are appropriate for codebase-specific specialists and should be checked into version control for team use. Source: [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents).
- Subagent frontmatter supports `name`, `description`, `tools`, `disallowedTools`, `model`, `permissionMode`, `maxTurns`, `skills`, `memory`, `hooks`, `background`, `isolation`, and `color`. Only `name` and `description` are required, but the optional fields are key to constraining capabilities and preloading skills. Source: [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents).
- Claude Code can preload skills into subagents via the subagent `skills` field; the full skill content is injected at startup for listed skills. Source: [Claude Code subagents docs](https://code.claude.com/docs/en/sub-agents).
- Claude Code skills live under `.claude/skills/<skill-name>/SKILL.md` and should be used for reusable workflows that are invoked on demand rather than always loaded. Anthropic’s blog distinguishes `CLAUDE.md` as always-loaded coordination from skills as reusable task workflows. Sources: [Claude Code skills docs](https://code.claude.com/docs/en/skills), [Anthropic subagents blog](https://claude.com/blog/subagents-in-claude-code).
- Project settings in `.claude/settings.json` are the official mechanism for permissions, hooks, environment variables, and tool behavior; many setting changes reload during a running session. Source: [Claude Code settings docs](https://code.claude.com/docs/en/settings).
- Hooks can run on subagent lifecycle events such as `SubagentStart` and `SubagentStop`, and broader hook events can validate commands, edits, or session state. Source: [Claude Code hooks docs](https://code.claude.com/docs/en/hooks).
- Claude Code configuration should be diagnosed with `/context`, `/memory`, `/skills`, `/agents`, `/hooks`, `/permissions`, `/doctor`, and `/status` to confirm what actually loaded. Source: [Claude Code debug configuration docs](https://code.claude.com/docs/en/debug-your-config).

## Current Inventory

### Always-loaded / coordination layer

- `CLAUDE.md` defines the unified engineering doctrine, turn-start ritual, project identity, stack, commands, architecture, invariants, FSV law, FDD law, security policy, testing policy, and technical debt notes.
- `.claude/rules/01-security.md` contains threat-model, prompt-injection, secrets, input-validation, and dependency-audit rules.
- `.claude/imports/doctrine-summary.md` and `.claude/output-styles/doctrine-engineer.md` provide doctrine and output-style support.

### Subagents

| Agent | Intended role | Current capability posture | Notable issue |
| --- | --- | --- | --- |
| `code-reviewer` | Five-dimension read-only review | `Read`, `Grep`, `Glob`; no writes or shell | Good separation of concerns; no preloaded review skill despite similarly named skill. |
| `fdd-investigator` | Root-cause / incident investigation | Read + Bash, no writes | Strong FDD fit; preloads valid-looking `forensic-debug` and `fsv-verify`, but `forensic-debug` frontmatter currently fails YAML parsing. |
| `security-auditor` | Security audit | Read-only, no shell | References missing skills `owasp-vulnerability-checker` and `dependency-audit`. |
| `ship` | Pre-merge fan-out coordinator | `Agent`, `Read`, `Glob` | Good orchestrator concept; should be paired with hooks/settings and have allowed subagent list tightened. |
| `test-engineer` | Test design/write/coverage analysis | Read/write/edit/bash | Overlaps heavily with `test-writer`; no explicit `skills` field. |
| `test-writer` | Pytest suites for DegenExus | Read/write/edit/bash; preloads `edge-case-audit`, `fsv-verify` | Contains stale issue references and overlaps with `test-engineer`. |

### Skills

| Skill path | Intended role | Current discovery risk |
| --- | --- | --- |
| `.claude/skills/code-reviewer/SKILL.md` | Code review workflow | **High:** YAML frontmatter indentation is invalid; fields after `tools` are nested incorrectly. |
| `.claude/skills/forensic-debug/SKILL.md` | Forensic debugging workflow | **High:** YAML frontmatter fails parsing because the long unquoted description contains colon-heavy trigger text. |
| `.claude/skills/edge-case-audit/SKILL.md` | Boundary/failure-mode reasoning | Low: frontmatter parses. |
| `.claude/skills/fsv-verify/SKILL.md` | Full State Verification workflow | Low: frontmatter parses. |
| `.claude/skills/code-reviewer/references/review-template.md` | Supporting reference | Expected to have no frontmatter. |
| `.claude/skills/test` | Empty/placeholder file | Medium: stray file can confuse maintainers; should be removed or converted into a real skill directory. |

### Slash commands

| Command | Intended role | Notable issue |
| --- | --- | --- |
| `/build` | Incremental implementation | References `agent-skills:*` names that are not present in this repo. |
| `/code-simplify` | Simplification workflow | References missing `agent-skills:code-simplification`. |
| `/plan` | Task planning | References missing `agent-skills:planning-and-task-breakdown`. |
| `/review` | Review workflow | References missing `agent-skills:code-review-and-quality`; duplicates local `code-reviewer` agent/skill naming. |
| `/ship` | Pre-launch fan-out | Good concept, but has generic web/app checks that do not match DegenExus terminal simulator as tightly as it could. |
| `/spec` | Spec-driven development | References missing `agent-skills:spec-driven-development`. |
| `/test` | TDD workflow | References missing `agent-skills:test-driven-development` and browser DevTools skill that are not present. |

## Priority Findings and Actions

### P0 — Fix skill discoverability before adding more automation

**Finding:** Two important skills appear to have invalid YAML frontmatter:

- `.claude/skills/code-reviewer/SKILL.md` has `disallowedTools`, `model`, `effort`, `permissionMode`, `maxTurns`, and `user-invocable` indented under the `tools` list rather than at the top level.
- `.claude/skills/forensic-debug/SKILL.md` uses a very long unquoted scalar with colon-containing trigger phrases; the YAML parser reports `mapping values are not allowed here`.

**Why it matters:** Skills are only useful if Claude Code can discover their frontmatter and decide when to load them. Invalid frontmatter makes the skill invisible or partially unusable, and can break `skills:` preloading from agents.

**Action plan:**

1. Convert every skill frontmatter block to a small, stable pattern:

   ```yaml
   ---
   name: forensic-debug
   description: >
     Activate for forensic debugging of software systems when symptoms indicate
     violated invariants, contradictory evidence, unreliable logs, production
     incidents, Heisenbugs, or causal timeline reconstruction.
   ---
   ```

2. Keep colons and quoted trigger phrases in the Markdown body rather than in a one-line YAML scalar.
3. Add a lightweight validation command to the repo documentation or hooks:

   ```bash
   python - <<'PY'
   from pathlib import Path
   import yaml
   for path in sorted(Path('.claude').rglob('*.md')):
       text = path.read_text()
       if text.startswith('---'):
           yaml.safe_load(text.split('---', 2)[1])
   PY
   ```

4. Treat invalid `.claude/**` frontmatter as a pre-merge blocker in `/ship`.

### P0 — Resolve missing skill references

**Finding:** Several agents and commands reference skills that do not exist locally:

- `security-auditor` references `owasp-vulnerability-checker` and `dependency-audit`.
- `/build`, `/code-simplify`, `/plan`, `/review`, `/spec`, and `/test` reference `agent-skills:*` names that are not represented in `.claude/skills/`.
- `/test` references browser DevTools, which is not aligned with this terminal-only simulator unless explicitly added as an external MCP workflow.

**Why it matters:** Missing skills create false confidence: command text says a reusable workflow was invoked, but there is no local skill for Claude Code to load.

**Action plan:**

1. Either create these local skills or rewrite commands to call existing project agents/skills.
2. Prefer project-specific names over generic `agent-skills:*` labels:
   - `agent-skills:test-driven-development` → `edge-case-audit` + `fsv-verify` + DegenExus pytest instructions.
   - `agent-skills:code-review-and-quality` → `code-reviewer` subagent plus code-reviewer skill once fixed.
   - `agent-skills:shipping-and-launch` → `ship` subagent.
3. If these names were intended to come from a plugin, document the plugin dependency in `CLAUDE.md` or `.claude/README.md` and add a `/doctor` verification step.

### P1 — Consolidate overlapping test roles

**Finding:** `test-engineer` and `test-writer` both write tests, both can edit files, and both use pytest concepts. `test-writer` is more DegenExus-specific, while `test-engineer` is broader.

**Why it matters:** Overlapping descriptions can reduce automatic delegation quality and create inconsistent test style.

**Recommended target state:**

- Keep **one write-capable test agent** named `test-engineer` for all test authoring.
- Fold DegenExus-specific requirements from `test-writer` into `test-engineer`:
  - FSV-AAA structure.
  - Use `pytest-mock` instead of `unittest.mock`.
  - Mock LLM calls.
  - Coverage target expectations.
  - Explicit `skills: [edge-case-audit, fsv-verify]`.
- Convert `test-writer` into either:
  - A read-only coverage-planning agent, or
  - A deprecated alias with a brief body: “Use `test-engineer` instead.”

**Action plan:**

1. Rename or merge to avoid two agents competing for “write tests” tasks.
2. Update `/ship` to fan out to the retained test agent only.
3. Move stale issue-specific content out of agent prompts and into a dated memory or audit note.

### P1 — Strengthen `/ship` as the central synergy orchestrator

**Finding:** `ship` has the right architecture — fan out to code, security, and test specialists — but its tool policy is broad (`Agent` without narrowing), and the slash command contains generic website launch checks that do not fit DegenExus.

**Why it matters:** The ship gate is the ideal place to make all specialists synergistic and consistent. It should be the highest-signal command for pre-merge validation.

**Action plan:**

1. Restrict the orchestrator’s agent tool to known child agents if supported in the current Claude Code version:

   ```yaml
   tools:
     - Agent(code-reviewer,security-auditor,test-engineer,fdd-investigator)
     - Read
     - Glob
   ```

2. Make `/ship` explicitly DegenExus-oriented:
   - Verify `python3 -m pytest tests/ -v` output.
   - Verify `python3 -m compileall -q src/` output.
   - Verify `python3 -m pyflakes src/` or equivalent if available.
   - Verify no prompt-injection regression in agent prompt construction.
   - Verify no secrets or SQLite DB files were introduced.
3. Add escalation logic:
   - If tests fail → spawn `fdd-investigator` read-only first, then a write-capable implementation agent only after root cause is known.
   - If security findings exist → block merge until `security-auditor` returns no Critical/High issues.
4. Require final output to include:
   - Go/no-go verdict.
   - Findings by agent.
   - Commands run and exact evidence.
   - Edge cases considered.
   - Whether memory files were updated.

### P1 — Add `.claude/settings.json` for enforceable project policy

**Finding:** The repository currently relies heavily on prose instructions in `CLAUDE.md`, agents, skills, and commands. There is no project settings file visible in the audited inventory.

**Why it matters:** Claude Code settings are the official path for permissions, hooks, environment variables, and tool behavior. Doctrine-critical behaviors should be automated where possible.

**Action plan:**

Create `.claude/settings.json` in a follow-up PR with conservative controls such as:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)",
      "Bash(cat .env*)",
      "Read(.env*)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python - <<'PY'\nfrom pathlib import Path\nimport yaml\nfor p in sorted(Path('.claude').rglob('*.md')):\n    t=p.read_text(errors='replace')\n    if t.startswith('---'):\n        yaml.safe_load(t.split('---',2)[1])\nPY"
          }
        ]
      }
    ]
  }
}
```

Tune the exact permission syntax after verifying with `/permissions` and `/doctor`.

### P1 — Add subagent lifecycle hooks for auditability

**Finding:** Claude Code supports `SubagentStart` and `SubagentStop` hooks. DegenExus has a strong audit culture, but there is no visible hook-based subagent activity log.

**Why it matters:** Agent fan-out is only trustworthy if the parent can later reconstruct which specialist ran, on what scope, and when.

**Action plan:**

1. Add a script such as `.claude/hooks/log-subagent-event.py` in a future PR.
2. Configure `SubagentStart` and `SubagentStop` hooks in `.claude/settings.json`.
3. Write append-only JSONL entries to a gitignored local path such as `.claude/local/subagent-events.jsonl`.
4. Include fields: timestamp, event, agent type, cwd, git SHA, changed files, and invocation scope.

### P1 — Reduce `CLAUDE.md` context load and move playbooks to skills

**Finding:** `CLAUDE.md` is comprehensive, but it includes long operational doctrine, known debt, command tables, architecture descriptions, and process law. Claude Code guidance indicates adherence drops when instruction files become vague, conflicting, or too long; debugging docs recommend `/context` and `/memory` to verify what actually loaded.

**Why it matters:** `CLAUDE.md` is always loaded. Long always-loaded content competes with task-specific content and increases the chance that critical rules are ignored.

**Action plan:**

1. Keep `CLAUDE.md` to durable, always-relevant items:
   - Project identity.
   - Top-level source-of-truth doctrine.
   - Mandatory safety/security invariants.
   - Commands.
   - Agent delegation policy.
2. Move long workflows into skills:
   - FSV details → `fsv-verify` skill.
   - FDD details → `forensic-debug` skill.
   - Security threat model → `security-audit` skill or `.claude/rules/01-security.md`.
   - Testing protocol → `test-engineering` skill.
3. Add a short “When to use specialists” section:
   - For code review, always use `code-reviewer` read-only.
   - For persistent failures, use `fdd-investigator` before edits.
   - For dependency/auth/prompt-safety questions, use `security-auditor`.
   - For tests, use `test-engineer` with `edge-case-audit` and `fsv-verify`.

### P2 — Add a `.claude/README.md` map

**Finding:** The `.claude` tree has agents, skills, rules, imports, commands, output styles, and memory, but no local map explaining how they fit together.

**Why it matters:** A short map helps human maintainers understand the intended synergy without reading every file.

**Action plan:**

Create `.claude/README.md` with:

- Directory purpose table.
- Agent matrix: name, write permission, default use, preloaded skills.
- Skill matrix: trigger, owner agent, maturity status.
- Command matrix: user-facing command, spawned agents, required evidence.
- Validation checklist: `/context`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`.

### P2 — Introduce DegenExus-specific specialist agents

The current agents are mostly generic engineering roles. DegenExus would benefit from specialists that mirror its real risk profile.

#### 1. `risk-gate-verifier`

**Purpose:** Read-only verification of `RiskGate`, `ExecutionGate`, `RiskDecision`, trade-level ordering, exposure limits, stale decisions, and bypass paths.

**Suggested frontmatter:**

```yaml
---
name: risk-gate-verifier
description: >
  Read-only DegenExus risk-control auditor. Use proactively for changes touching
  risk gates, execution gates, trade proposals, portfolio exposure, position
  sizing, stop-loss/take-profit logic, or stale RiskDecision handling.
tools: [Read, Grep, Glob, Bash]
disallowedTools: [Write, Edit, MultiEdit, Agent]
model: sonnet
effort: high
permissionMode: dontAsk
skills: [edge-case-audit, fsv-verify]
memory: project
---
```

**Core checks:**

- No path from proposal to execution skips hard gate validation.
- `RiskDecision.expires_at` is enforced.
- LONG/SHORT stop-loss and take-profit ordering remains correct.
- Total exposure and max open positions cannot be bypassed.
- Tests include boundary values for every risk limit.

#### 2. `prompt-injection-auditor`

**Purpose:** Read-only review of prompt construction and cross-agent text flow.

**Suggested checks:**

- Every prior-agent reasoning field injected into a prompt is sanitized.
- Market data strings and LLM outputs are treated as untrusted.
- New prompt templates do not weaken system instructions.
- Prompt-injection patterns have regression tests.

#### 3. `trade-lifecycle-auditor`

**Purpose:** Verify state-machine transitions, partial take-profit behavior, and SQLite audit state.

**Suggested checks:**

- Terminal states cannot transition.
- Partial close dedup survives restart.
- `upsert_trade` updates all intended mutable fields.
- DB rows, not return values, are used as SoT evidence in tests.

#### 4. `market-data-integrity-auditor`

**Purpose:** Audit yfinance/indicator ingestion boundaries.

**Suggested checks:**

- OHLCV validation happens at Pydantic boundaries.
- Missing/NaN/zero-volume bars are handled deterministically.
- Indicator warmup periods are explicit.
- Network failures degrade through deterministic fallback paths.

#### 5. `docs-memory-curator`

**Purpose:** Keep `CLAUDE.md`, `AGENTS.md`, `memory/`, issue references, and PR templates in sync.

**Suggested checks:**

- No closed issues remain listed as active debt.
- `CLAUDE.md` and `AGENTS.md` agree on Python version and commands.
- Memory updates are append-only, dated, and scoped.
- PR body requirements are satisfied.

### P2 — Introduce synergy-oriented skills

#### 1. `claude-config-audit`

A skill that audits `.claude/**` itself.

**Workflow:**

1. Parse all Markdown frontmatter.
2. List all agents and skills.
3. Cross-check every `skills:` reference against `.claude/skills/*/SKILL.md`.
4. Cross-check slash-command references to local skills/agents/plugins.
5. Report invalid YAML, missing references, duplicate names, and broad permissions.

#### 2. `risk-control-audit`

A reusable workflow for `risk-gate-verifier`, `code-reviewer`, and `/ship`.

**Workflow:** enumerate risk invariants, map them to source files/tests, verify SoT evidence, and produce a PASS/BLOCK verdict.

#### 3. `prompt-safety-review`

A reusable workflow for `security-auditor` and `prompt-injection-auditor`.

**Workflow:** trace untrusted text sources, verify sanitization before prompt injection, and recommend regression tests.

#### 4. `sqlite-sot-verify`

A reusable workflow for DB-backed FSV.

**Workflow:** capture pre-state rows, perform operation, read rows directly, compute expected delta, and reject ORM/self-report-only proof.

#### 5. `release-evidence-pack`

A workflow for producing PR evidence.

**Workflow:** collect test output, coverage, lint, compile, security audit, edge cases, changed files, memory updates, and PR-template sections.

### P2 — Make agent memory useful or remove it

**Finding:** `.claude/agent-memory/*/memory.md` files exist but are mostly empty. They are a good concept, but empty memory adds maintenance surface without improving behavior.

**Action plan:**

1. Add a “memory write criteria” section to each agent:
   - Write only recurring patterns, false positives, and stable project facts.
   - Do not write one-off task details.
   - Include date and source evidence.
2. Rename `security-reviewer` memory to match `security-auditor`, or explicitly document that it is historical.
3. Add `project` memory to any agents intended to learn across this repo.

### P3 — Normalize naming and descriptions

**Finding:** Names and descriptions mix generic skill names, local agent names, plugin-like `agent-skills:*` names, and stale issue-specific text.

**Action plan:**

1. Use one vocabulary:
   - Agents: noun roles (`code-reviewer`, `security-auditor`, `test-engineer`).
   - Skills: workflow verbs/nouns (`fsv-verify`, `edge-case-audit`, `risk-control-audit`).
   - Commands: user actions (`/review`, `/ship`, `/test`).
2. Add “Use proactively” phrasing to descriptions where automatic delegation is desired.
3. Remove stale issue numbers from agent descriptions; keep issue-specific work in memory or task files.

## Proposed Target Architecture

```text
CLAUDE.md
  ├─ Always-loaded doctrine and delegation policy
  ├─ Points to .claude/rules/01-security.md for security specifics
  └─ Points to skills for long workflows

.claude/settings.json
  ├─ Permission deny rules for secrets/destructive commands
  ├─ Hooks for frontmatter validation and subagent audit events
  └─ Optional env defaults for Claude Code behavior

.claude/agents/
  ├─ ship                  # orchestrator; spawns only approved specialists
  ├─ code-reviewer          # read-only quality review
  ├─ security-auditor       # read-only security review
  ├─ test-engineer          # write-capable test authoring
  ├─ fdd-investigator       # read-only root-cause analysis
  ├─ risk-gate-verifier     # read-only risk-control specialist
  ├─ prompt-injection-auditor
  ├─ trade-lifecycle-auditor
  ├─ market-data-integrity-auditor
  └─ docs-memory-curator

.claude/skills/
  ├─ claude-config-audit/
  ├─ code-reviewer/
  ├─ edge-case-audit/
  ├─ forensic-debug/
  ├─ fsv-verify/
  ├─ prompt-safety-review/
  ├─ risk-control-audit/
  ├─ release-evidence-pack/
  └─ sqlite-sot-verify/

.claude/commands/
  ├─ review.md   # invokes code-reviewer + relevant skills
  ├─ test.md     # invokes test-engineer workflow
  ├─ ship.md     # invokes ship orchestrator
  ├─ audit.md    # invokes claude-config-audit and repo checks
  └─ plan.md     # read-only planning, no unexpected file writes
```

## Implementation Roadmap

### Phase 1 — Make the current setup load reliably

1. Fix invalid YAML frontmatter in `code-reviewer` and `forensic-debug` skills.
2. Remove or convert `.claude/skills/test`.
3. Add a `claude-config-audit` skill or script-based validation command.
4. Run `/skills`, `/agents`, and `/doctor` in Claude Code and record results.

**Exit criteria:** all local skills appear in `/skills`; all agents appear in `/agents`; `/doctor` has no schema errors.

### Phase 2 — Eliminate broken references and role overlap

1. Resolve missing `security-auditor` skill references.
2. Rewrite commands away from missing `agent-skills:*` references or document plugin requirements.
3. Merge `test-writer` into `test-engineer` or deprecate one role.
4. Update `/ship` to use the final agent set.

**Exit criteria:** every `skills:` entry maps to an existing local/plugin skill; every slash command references available agents/skills only.

### Phase 3 — Add enforcement

1. Add `.claude/settings.json` with conservative permissions.
2. Add hooks for frontmatter validation after `.claude/**` edits.
3. Add subagent lifecycle logging.
4. Add `/audit` command for Claude setup verification.

**Exit criteria:** a bad skill frontmatter edit is caught immediately; subagent runs leave auditable local evidence.

### Phase 4 — Add DegenExus-specific specialists

1. Add `risk-gate-verifier`.
2. Add `prompt-injection-auditor`.
3. Add `trade-lifecycle-auditor`.
4. Add `market-data-integrity-auditor`.
5. Add `docs-memory-curator`.

**Exit criteria:** `/ship` can fan out to generic quality, security, tests, and domain-risk specialists.

### Phase 5 — Slim and stratify context

1. Shorten `CLAUDE.md` to high-salience rules.
2. Move long protocols into skills.
3. Add `.claude/README.md` as an internals map.
4. Verify context load with `/context`.

**Exit criteria:** `CLAUDE.md` is shorter, clearer, and delegates long workflows to discoverable skills.

## Concrete Backlog

| Priority | Item | Files to change in future PR | Acceptance criteria |
| --- | --- | --- | --- |
| P0 | Repair invalid skill YAML | `.claude/skills/code-reviewer/SKILL.md`, `.claude/skills/forensic-debug/SKILL.md` | YAML parse succeeds for all frontmatter; skills visible in `/skills`. |
| P0 | Remove missing skill refs | `.claude/agents/security-auditor.md`, `.claude/commands/*.md` | No `skills:` entry or command invocation points to a nonexistent local/plugin skill. |
| P1 | Consolidate test agents | `.claude/agents/test-engineer.md`, `.claude/agents/test-writer.md`, `.claude/commands/test.md`, `.claude/commands/ship.md` | One authoritative write-capable test role remains. |
| P1 | Add project settings | `.claude/settings.json` | `/permissions` and `/hooks` show expected policy; `/doctor` clean. |
| P1 | Add subagent audit hooks | `.claude/settings.json`, `.claude/hooks/*` | `SubagentStart` and `SubagentStop` create local audit records. |
| P2 | Add config audit skill | `.claude/skills/claude-config-audit/SKILL.md` | Skill reports invalid YAML, duplicate agent names, missing skills, and broad permissions. |
| P2 | Add risk specialist | `.claude/agents/risk-gate-verifier.md`, `.claude/skills/risk-control-audit/SKILL.md` | Risk-related changes trigger read-only risk gate review. |
| P2 | Add prompt safety specialist | `.claude/agents/prompt-injection-auditor.md`, `.claude/skills/prompt-safety-review/SKILL.md` | Prompt changes trigger sanitization-path review. |
| P2 | Add lifecycle specialist | `.claude/agents/trade-lifecycle-auditor.md`, `.claude/skills/sqlite-sot-verify/SKILL.md` | DB/trade-state changes get direct SoT verification. |
| P2 | Add internals map | `.claude/README.md` | Maintainers can identify each agent/skill/command purpose from one file. |
| P3 | Slim `CLAUDE.md` | `CLAUDE.md`, `.claude/imports/*`, `.claude/skills/*` | Always-loaded context contains only durable high-salience rules. |

## Validation Commands for Future PRs

Use these checks after making any `.claude/**` changes:

```bash
python - <<'PY'
from pathlib import Path
import yaml
for path in sorted(Path('.claude').rglob('*.md')):
    text = path.read_text(errors='replace')
    if text.startswith('---'):
        yaml.safe_load(text.split('---', 2)[1])
print('frontmatter ok')
PY
```

```bash
python - <<'PY'
from pathlib import Path
import yaml
skills = {p.parent.name for p in Path('.claude/skills').glob('*/SKILL.md')}
missing = []
for agent in sorted(Path('.claude/agents').glob('*.md')):
    text = agent.read_text(errors='replace')
    if not text.startswith('---'):
        continue
    fm = yaml.safe_load(text.split('---', 2)[1]) or {}
    for skill in fm.get('skills', []) or []:
        if skill not in skills:
            missing.append((str(agent), skill))
if missing:
    for agent, skill in missing:
        print(f'missing skill: {agent} -> {skill}')
    raise SystemExit(1)
print('agent skill references ok')
PY
```

Also run inside Claude Code after changes:

```text
/context
/memory
/agents
/skills
/hooks
/permissions
/doctor
/status
```

## Final Recommendation

Treat the Claude setup as a first-class subsystem with its own tests. The repo already has a sophisticated doctrine and several useful specialist definitions, but it will become much more reliable after the discovery layer is fixed, stale references are removed, write-capable roles are consolidated, and hooks/settings enforce what prose currently asks agents to remember.

The highest-return next PR should be narrowly scoped: **repair skill YAML, remove missing skill references, add a Claude-config audit skill/check, and update `/ship` to report config health before doing code review.** After that, add DegenExus-specific risk and prompt-safety specialists so the agent system reflects the actual hazards of a multi-agent trading simulator rather than only generic software-engineering roles.
