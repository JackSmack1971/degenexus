# Claude Code Internals Audit — Actionable Improvement Plan

**Date:** 2026-05-28
**Scope:** `CLAUDE.md`, `.claude/README.md`, `.claude/settings.json`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/rules/`, `.claude/imports/`, `.claude/output-styles/`, `.claude/hooks/`, and `.claude/agent-memory/`.
**Deliverable constraint:** Recommendations only. This refresh intentionally modifies no Claude Code internals other than replacing this audit file.

## Research Baseline

This audit refresh compared the repository's Claude Code setup with current public Claude Code documentation and then verified the local files on disk.

### External references consulted

- Claude Code feature overview: <https://code.claude.com/docs/en/features-overview>
  - Key point applied here: `CLAUDE.md` is best for always-on context, skills for on-demand workflows, subagents for isolation, and hooks for automation.
- Claude Code skills documentation: <https://code.claude.com/docs/en/skills>
  - Key points applied here: skills load only when used, skills can be invoked as slash commands, custom commands still work, and skills are preferred when supporting files or richer frontmatter are useful.
- Claude Code subagents documentation: <https://code.claude.com/docs/en/sub-agents>
  - Key points applied here: subagents can preload skills through `skills:`, can use persistent project memory at `.claude/agent-memory/<agent>/MEMORY.md`, and the full content of preloaded skills enters the subagent's startup context.
- Claude Code hooks documentation: <https://code.claude.com/docs/en/hooks>
  - Key points applied here: hooks run at lifecycle events, can block or decide tool use, and agent hooks are available when verification requires file or output inspection.
- Claude Code settings/configuration documentation: <https://code.claude.com/docs/en/configuration>
  - Key points applied here: `.claude/settings.json` is the shared project settings layer, `permissions.deny` is the recommended mechanism for excluding secrets, and settings can also express sandbox, network, plugin, attribution, and default-agent behavior.
- Claude Code permissions documentation: <https://code.claude.com/docs/en/permissions>
  - Key points applied here: permission deny rules are evaluated before allow rules, hooks do not bypass permission rules, and file permission rules are not a substitute for OS-level sandboxing when subprocesses can read files indirectly.

### Local evidence commands run

```bash
find .. -name AGENTS.md -print
find .claude -maxdepth 4 -type f | sort | sed 's#^./##'
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
python - <<'PY'
from pathlib import Path
import yaml
for p in sorted(Path('.claude/agents').glob('*.md')):
    text = p.read_text()
    fm = yaml.safe_load(text.split('---', 2)[1]) or {}
    mem = Path('.claude/agent-memory') / fm.get('name', p.stem) / 'MEMORY.md'
    print(f"{fm.get('name', p.stem)} skills={fm.get('skills', [])} memory={mem.exists()}")
PY
python - <<'PY'
from pathlib import Path
import yaml
for p in sorted(Path('.claude/skills').glob('*/SKILL.md')):
    text = p.read_text()
    fm = yaml.safe_load(text.split('---', 2)[1]) or {}
    print(p.parent.name, 'disable-model-invocation=', fm.get('disable-model-invocation', False), 'lines=', len(text.splitlines()))
PY
```

## Executive Summary

The stale findings about missing project memory files and broken skill references should be removed. The current setup validates successfully, every checked-in project subagent with `memory: project` has a corresponding uppercase `MEMORY.md`, and the agent/skill inventory is coherent.

The next improvements should focus on **stronger synergy, smaller context payloads, and enforceable safety boundaries**:

1. **Turn the current agent/skill map into a machine-checkable contract.** The repository has a strong human-readable synergy map, but commands, agents, and validation still rely on prose. A small JSON/YAML contract would let hooks and `/ship` verify that each risk surface has exactly one primary specialist, required skills, and required evidence fields.
2. **Move mature slash commands into skill directories.** Claude Code now treats skills and custom commands similarly, but skills support supporting files, richer invocation controls, and progressive disclosure. The current `.claude/commands/*.md` files are concise and valid, but high-value commands such as `ship`, `audit`, `review`, and `test` would be more reusable as skill-backed workflows.
3. **Tighten permission and sandbox recommendations.** The current settings deny obvious `.env` reads and destructive shell patterns, but they do not block `Edit(.env*)`, do not add a `PreToolUse` protected-file guard, and do not define sandbox/network boundaries for subprocesses.
4. **Reduce accidental model invocation for broad skills.** Skills like `edge-case-audit` and `fsv-verify` are valuable, but their descriptions are broad enough to trigger frequently. Keep them available, but make activation more explicit or split always-needed doctrine from expensive audit workflows.
5. **Make release evidence deterministic.** `/ship` describes the desired fan-out, but the evidence shape returned by each specialist is not schema-checked. Add a shared evidence schema and make the validator check that all agent prompts and commands require it.

## Current Inventory Snapshot

### Project instruction layer

- `CLAUDE.md` is concise and appropriately delegates long workflows to `.claude/skills/`, `.claude/README.md`, and `.claude/rules/02-agent-synergy.md`.
- `.claude/README.md` correctly treats `.claude/` as a first-class subsystem and documents validation commands, directory purposes, agent matrix, and skill matrix.
- `.claude/rules/01-security.md` and `.claude/rules/02-agent-synergy.md` provide supplemental durable rules rather than bloating `CLAUDE.md`.

### Agents

There are 11 project subagents:

| Agent | Main role | Current strengths | Main improvement target |
| --- | --- | --- | --- |
| `ship` | Release coordinator | Has explicit main-session warning and specialist fan-out list. | Add structured evidence schema and validator coverage for its required subagent roster. |
| `code-reviewer` | Read-only five-axis review | Concise prompt and preloaded `code-reviewer` skill. | Add standard handoff fields for domain-specialist escalation. |
| `security-auditor` | Read-only security review | Preloads security, prompt-safety, and config-audit skills. | Consider read-only `Bash` or explicit dependency-audit handoff so it can verify security evidence instead of only reading files. |
| `test-engineer` | Test authoring and coverage | Write-capable with test and FSV skills. | Clarify when it may write tests versus when it should only report coverage gaps. |
| `test-writer` | Minimal test suggestion agent | Very small, low-turn prompt. | Merge into `test-engineer` or preload `test-regression`; otherwise it overlaps without shared doctrine. |
| `fdd-investigator` | Root-cause falsification | Strong read-only forensic workflow. | Add required handoff output for when it escalates from root cause to implementer. |
| `risk-gate-verifier` | Risk-control audit | Strong fit for trading simulator invariants. | Add machine-readable ownership of `RiskGate`, `ExecutionGate`, sizing, expiry, and bypass surfaces. |
| `prompt-injection-auditor` | Prompt and context safety | Explicitly treats text as evidence, not instructions. | Add required prompt-flow trace format shared with `prompt-safety-review`. |
| `trade-lifecycle-auditor` | SQLite/trade persistence | Preloads SQLite source-of-truth verification. | Add direct required DB evidence fields for lifecycle transitions. |
| `market-data-integrity-auditor` | OHLCV/indicator/data failure audit | Strong deterministic failure-mode coverage. | Add explicit ownership of live-network isolation and yfinance mocks. |
| `docs-memory-curator` | Docs and memory consistency | Preloads config-audit and release evidence. | Make it the owner of the future machine-readable synergy contract. |

### Skills

There are 13 project skills. Four are already manual-only through `disable-model-invocation: true`: `claude-config-audit`, `dependency-audit`, `release-evidence-pack`, and `run-degenexus`. The remaining nine are model-invocable.

High-value reusable workflow skills:

- `fsv-verify`
- `forensic-debug`
- `edge-case-audit`
- `test-regression`
- `code-reviewer`
- `security-review`
- `prompt-safety-review`
- `risk-control-audit`
- `sqlite-sot-verify`

### Hooks and settings

- `.claude/settings.json` has project-level deny rules for destructive shell patterns, `.env` reads, and `.env` writes through shell echo patterns.
- Hooks currently cover `PostToolUse`, `SubagentStart`, `SubagentStop`, `ConfigChange`, `SessionStart`, and `FileChanged`.
- The local validator passes and hooks compile.

## Findings and Actionable Improvements

### P0 — No immediate broken-internals blocker found

**Finding:** The current configuration is valid under the local validator. Project memory files use the documented uppercase `MEMORY.md` form, and all agent skill references resolve to checked-in skills.

**Evidence:** `python .claude/hooks/validate-claude-config.py` returned `claude config validation ok`; `python -m compileall -q .claude/hooks` completed successfully; every agent memory directory contains `MEMORY.md`.

**Action:** Remove stale remediation work about missing uppercase memory files or missing skill references from planning queues. Keep the validator check in release gates.

---

### P1 — Add a machine-readable agent/skill synergy contract

**Problem:** `.claude/rules/02-agent-synergy.md`, `.claude/README.md`, and command files describe specialist routing in prose. Prose is useful for humans but hard for hooks or validators to enforce.

**Why it matters:** The repository's doctrine depends on correct delegation. If a command forgets to invoke `prompt-injection-auditor` for prompt-template changes, or `risk-gate-verifier` for execution changes, the omission is hard to catch automatically.

**Recommended change:** Add a checked-in contract file such as `.claude/rules/synergy-contract.yml` or `.claude/synergy.json` with this structure:

```yaml
risk_surfaces:
  prompt_safety:
    primary_agent: prompt-injection-auditor
    required_skills:
      - prompt-safety-review
      - edge-case-audit
    file_globs:
      - "src/**/*prompt*"
      - "src/agents/**/*.py"
      - ".claude/agents/*.md"
      - ".claude/skills/*/SKILL.md"
    required_evidence:
      - prompt_flow_trace
      - sanitizer_boundary
      - regression_tests
  risk_controls:
    primary_agent: risk-gate-verifier
    required_skills:
      - risk-control-audit
      - fsv-verify
    file_globs:
      - "src/core/risk*.py"
      - "src/core/execution*.py"
    required_evidence:
      - pre_state
      - post_state
      - expected_delta
```

**Acceptance criteria:**

- `validate-claude-config.py` verifies that every `primary_agent` exists.
- It verifies every listed skill exists.
- It verifies `/ship`, `/review`, `/audit`, and `/test` mention or load the contract rather than duplicating divergent prose.
- It verifies each agent prompt requires the evidence fields owned by that agent.

**Suggested owner:** `docs-memory-curator` with review from `ship` and `code-reviewer`.

---

### P1 — Strengthen protected-file enforcement beyond current `.env` deny rules

**Problem:** The current settings deny `Read(.env*)`, `Bash(cat .env*)`, and `Bash(echo * > .env*)`, but they do not explicitly deny `Edit(.env*)`, `Write(.env*)`, or broader secret paths such as `secrets/**`, `*.pem`, `*.key`, and credential JSON files. They also rely on Bash pattern matching for some shell operations.

**Why it matters:** Claude Code permission rules are useful, but the permissions documentation notes that file rules do not cover arbitrary subprocesses that read files indirectly. For a trading simulator with provider API keys, defense-in-depth should include explicit `Read`/`Edit` denies plus a `PreToolUse` protected-file hook.

**Recommended change:** In a future internals patch, extend `.claude/settings.json` and add a protected-file hook.

Suggested deny expansion:

```json
{
  "permissions": {
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)",
      "Read(./**/*.pem)",
      "Read(./**/*.key)",
      "Edit(./.env)",
      "Edit(./.env.*)",
      "Edit(./secrets/**)",
      "Edit(./**/*.pem)",
      "Edit(./**/*.key)",
      "Bash(rm -rf *)",
      "Bash(git push --force*)"
    ]
  }
}
```

Suggested hook addition:

- Add `.claude/hooks/protect-sensitive-files.py`.
- Register it on `PreToolUse` for `Read|Write|Edit|MultiEdit|Bash`.
- Have it block paths matching `.env*`, `secrets/**`, `*.pem`, `*.key`, SQLite DB/WAL/SHM files, and any future credential manifests.

**Acceptance criteria:**

- Attempts to read or edit `.env`, `.env.local`, `secrets/foo`, and `private.pem` are blocked before tool execution.
- The hook returns machine-readable blocking output and a human-readable remediation message.
- `validate-claude-config.py` checks that protected-file deny patterns and the hook registration remain present.

**Suggested owner:** `security-auditor` with `docs-memory-curator` validating settings syntax.

---

### P1 — Make `/ship` evidence schema-checkable

**Problem:** `/ship` and the `ship` subagent request many kinds of evidence, but each specialist is free to return narrative output. This makes release decisions harder to compare across runs.

**Why it matters:** DegenExus doctrine emphasizes source-of-truth verification. A release coordinator should not infer whether a specialist performed PRE/POST/DIFF or whether edge cases were considered; it should receive those fields explicitly.

**Recommended change:** Add `.claude/references/evidence-schema.md` or `.claude/rules/evidence-schema.yml` and require all agents to emit it.

Suggested minimal evidence fields:

```yaml
verdict: PASS | BLOCK | NEEDS_INFO
scope_reviewed: []
source_of_truth:
  files: []
  runtime_state: []
commands_run:
  - command: ""
    result: PASS | FAIL | WARNING | NOT_RUN
    reason: ""
findings:
  critical: []
  important: []
  suggestions: []
edge_cases:
  - name: ""
    covered_by: test | reasoning | not_covered
handoffs:
  - agent: ""
    reason: ""
memory_update:
  needed: true | false
  path: ""
```

**Acceptance criteria:**

- `ship` rejects a specialist result that lacks `verdict`, `scope_reviewed`, `source_of_truth`, and `findings`.
- `release-evidence-pack` uses the same schema.
- `docs-memory-curator` audits PR text against the schema.

**Suggested owner:** `ship` and `docs-memory-curator`.

---

### P2 — Convert mature slash commands into skills with supporting files

**Problem:** `.claude/commands/` still works, but Claude Code documentation now positions skills as the richer mechanism: skills can be slash-invoked, auto-invoked, packaged with references/scripts, and controlled with frontmatter such as `disable-model-invocation`.

**Why it matters:** `ship`, `audit`, `review`, and `test` are not just shortcuts; they are repeatable workflows with evidence templates and specialist routing. Keeping them as single command files encourages duplication and limits progressive disclosure.

**Recommended change:** Convert commands gradually, not all at once:

1. Create `.claude/skills/ship/SKILL.md` with `disable-model-invocation: true`.
2. Move reusable evidence details into `.claude/skills/ship/references/evidence-schema.md`.
3. Keep `.claude/commands/ship.md` as a thin compatibility shim that says: `Invoke /ship skill and follow .claude/rules/02-agent-synergy.md`.
4. Repeat for `audit`, `review`, and `test`.

**Acceptance criteria:**

- `/ship`, `/audit`, `/review`, and `/test` remain available.
- Their canonical workflow lives in skill directories.
- `validate-claude-config.py` warns if command and skill content diverge.
- Supporting references are loaded only when the skill is used.

**Suggested owner:** `docs-memory-curator`.

---

### P2 — Tune broad model-invocable skills to avoid accidental context inflation

**Problem:** The model-invocable skills `edge-case-audit` and `fsv-verify` intentionally describe broad triggers. This is helpful for safety but can cause frequent activation and load long workflow content into context.

**Why it matters:** Claude Code documentation emphasizes that skills save context because their bodies load only when used. If very broad descriptions cause automatic activation too often, that benefit is reduced.

**Recommended change:** Split broad skills into small doctrine skills plus heavier manual workflows:

- Keep a short model-invocable `fsv-doctrine` or slim `fsv-verify` skill with the PRE → ACT → POST → DIFF → HALT rule.
- Move the full adversarial checklist into `fsv-verify-deep` with `disable-model-invocation: true`.
- Shorten `edge-case-audit`'s description to a neutral trigger and move the long activation wording into `when_to_use` or references.
- Add validator warnings for descriptions above a chosen threshold, such as 300 characters for model-invocable skills.

**Acceptance criteria:**

- Routine implementation turns still see the FSV doctrine.
- Deep audit checklists load only when explicitly invoked or preloaded by the relevant specialist.
- `/skills` remains readable and has less trigger ambiguity.

**Suggested owner:** `docs-memory-curator`, reviewed by `test-engineer` and `risk-gate-verifier`.

---

### P2 — Clarify `security-auditor` evidence authority

**Problem:** `security-auditor` is read-only and does not include `Bash`, but it preloads `claude-config-audit`, which is a manual skill that commonly needs to run `python .claude/hooks/validate-claude-config.py`, and it owns dependency/security evidence that often requires commands.

**Why it matters:** A security reviewer that cannot run read-only commands must either trust parent-provided output or issue a handoff. That is acceptable, but the prompt should make the boundary explicit.

**Recommended change:** Choose one of two patterns:

- **Read-only evidence consumer:** Keep no `Bash`, but require the parent or `ship` to provide outputs from config validation, `pip-audit`, and secret scans.
- **Read-only command verifier:** Add `Bash` but constrain prompt and settings to read-only commands such as `python .claude/hooks/validate-claude-config.py`, `python -m compileall -q .claude/hooks`, `git diff --check`, and `pip-audit -r requirements.txt` when relevant.

**Acceptance criteria:**

- `security-auditor` output states whether it personally ran evidence commands or consumed parent-provided evidence.
- `ship` knows which evidence commands it must run before invoking a no-Bash security audit.
- `dependency-audit` ownership is explicit.

**Suggested owner:** `security-auditor`.

---

### P2 — Resolve `test-writer` versus `test-engineer` overlap

**Problem:** `test-writer` is a minimal low-turn agent with no preloaded skills, while `test-engineer` owns test authoring with `test-regression`, `edge-case-audit`, and `fsv-verify`. The distinction is not obvious in the synergy map.

**Why it matters:** Overlapping agents create routing uncertainty. If a command chooses the lightweight agent for a behavioral change, it may miss project testing doctrine.

**Recommended change:** Pick one strategy:

1. **Deprecate `test-writer`:** Remove it after updating references to use `test-engineer` for all test work.
2. **Specialize `test-writer`:** Make it read-only and explicitly limited to producing test-case lists, never editing files. Preload `test-regression` or a slim test-planning skill.

**Acceptance criteria:**

- `.claude/rules/02-agent-synergy.md` states exactly when to use each test agent.
- `validate-claude-config.py` warns if an agent with `test` in the name has no test skill and no explicit rationale.
- `/test` routes to only one canonical owner unless the user asks for a lightweight plan.

**Suggested owner:** `test-engineer` and `docs-memory-curator`.

---

### P2 — Add validator coverage for newer Claude Code settings and schema drift

**Problem:** The local validator already checks many repository-specific invariants, but current Claude Code docs include additional settings surfaces that are not checked: sandbox settings, network/domain restrictions, plugin settings, default `agent`, attribution, and protected-file path syntax.

**Why it matters:** `.claude/settings.json` is executable workflow configuration. Schema drift or broad permissions can silently weaken safety.

**Recommended change:** Extend `.claude/hooks/validate-claude-config.py` to check:

- Unknown top-level `.claude/settings.json` keys.
- Missing `Edit` denies for any protected `Read` deny path.
- Missing `PreToolUse` hook for sensitive files if protected-file policy is adopted.
- Network/sandbox policy presence or an explicit documented waiver.
- Whether command shims have matching skill directories after migration.
- Whether broad model-invocable skills exceed the selected description-length threshold.
- Whether every `Agent(...)` tool reference points to an existing project or documented external agent.

**Acceptance criteria:**

- Validator keeps returning zero errors on the current intended config.
- New warnings are actionable and suppressible only through an explicit documented waiver.
- CI or `/ship` runs the validator when any `.claude/**` file changes.

**Suggested owner:** `docs-memory-curator`.

---

### P3 — Add local Claude Code smoke-test transcript guidance

**Problem:** `.claude/README.md` recommends interactive checks such as `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status`, but there is no template for recording the results.

**Why it matters:** These commands can catch live Claude Code discovery issues that static validation cannot, especially skill visibility and hook loading.

**Recommended change:** Add a short evidence template, likely under `.claude/skills/claude-config-audit/references/live-smoke-template.md`:

```markdown
# Claude Code Live Smoke Evidence

Date:
Claude Code version:
Working directory:

- /status:
- /agents:
- /skills:
- /hooks:
- /permissions:
- /doctor:

Findings:
Follow-up issues:
```

**Acceptance criteria:**

- `claude-config-audit` prompts for this template after internals changes.
- `/ship` requires live smoke evidence only when `.claude/**`, `CLAUDE.md`, or `AGENTS.md` changed.

**Suggested owner:** `docs-memory-curator`.

---

### P3 — Document project memory curation thresholds per agent

**Problem:** Claude Code loads only an initial portion of project agent memory. The current memory files exist, but the audit did not find per-agent curation thresholds or summaries in a shared policy.

**Why it matters:** Project memory can silently become less useful as it grows. Important facts should stay in the first summary section, while historical details can move lower or into references.

**Recommended change:** Add a memory convention to `.claude/README.md` or `.claude/rules/02-agent-synergy.md`:

- First section: `Current operating assumptions`.
- Second section: `Recent validated learnings`.
- Third section: `Historical notes`.
- Require curators to keep the first 200 lines concise.

**Acceptance criteria:**

- `docs-memory-curator` audits memory files for the convention.
- Validator warns if a `MEMORY.md` exceeds a chosen soft line limit without a top summary section.

**Suggested owner:** `docs-memory-curator`.

## Suggested Implementation Sequence

1. **Create the synergy contract** and update validator checks for agent/skill existence.
2. **Add the evidence schema** and update `ship`, `release-evidence-pack`, and core agents to emit it.
3. **Strengthen protected-file controls** with expanded deny rules and a `PreToolUse` hook.
4. **Convert `/ship` to a skill-backed workflow**, then migrate `/audit`, `/review`, and `/test`.
5. **Tune broad skills** to reduce accidental activation and context inflation.
6. **Resolve `test-writer` ownership** by either deprecating it or making it a test-planning-only specialist.
7. **Extend live smoke evidence** for interactive Claude Code checks after internals changes.

## Definition of Done for the Next Internals Improvement PR

A follow-up implementation PR should include:

- Updated `.claude/**` files for the selected improvement.
- `python .claude/hooks/validate-claude-config.py` output.
- `python -m compileall -q .claude/hooks` output.
- If settings or hooks changed, a negative test or manual evidence showing a protected action is blocked.
- If agents or skills changed, `/agents` and `/skills` live smoke evidence or a documented reason it could not be run in the environment.
- At least three edge cases, including one prompt-injection/security edge, one missing-file/config edge, and one stale-memory/context edge.

## Stale Findings Removed

The following stale findings should no longer be carried forward:

- **Missing uppercase project memory files:** current project agent memory files are uppercase `MEMORY.md`.
- **Missing skill references from agents:** the current validator reports no missing skill references.
- **No `.claude/settings.json`:** project settings now exist and include permissions and hooks.
- **Commands referencing removed `agent-skills:*` plugin names:** the validator no longer reports stale plugin references.
- **Broken Claude internals validation:** `validate-claude-config.py` currently passes.

---

## Implementation PR Map — 2026-05-28

This section maps every finding above to the single implementation PR that closes it. Downstream agents should treat the files below as the new source-of-truth implementation and run `python .claude/hooks/validate-claude-config.py` plus `python -m compileall -q .claude/hooks` before review.

| Finding | Status | Implementation source of truth |
| --- | --- | --- |
| P0 — no immediate broken-internals blocker | Preserved | Validator remains the release gate in `.claude/hooks/validate-claude-config.py`; no stale missing-memory or missing-skill work is reintroduced. |
| P1 — machine-readable agent/skill synergy contract | Addressed | `.claude/rules/synergy-contract.yml` defines risk surfaces, primary agents, required skills, globs, evidence fields, and command-contract references. `.claude/hooks/validate-claude-config.py` validates agent existence, skill existence, command references, and agent-owned evidence fields. |
| P1 — stronger protected-file enforcement | Addressed | `.claude/settings.json` expands `Read`/`Edit`/`Write` deny rules for `.env*`, `secrets/**`, key/cert/credential JSON, and SQLite runtime files. `.claude/hooks/protect-sensitive-files.py` blocks protected `Read`, `Write`, `Edit`, `MultiEdit`, and `Bash` tool calls at `PreToolUse`. |
| P1 — schema-checkable `/ship` evidence | Addressed | `.claude/rules/evidence-schema.yml` defines required evidence fields. `.claude/skills/ship/SKILL.md`, `.claude/agents/ship.md`, and `.claude/skills/release-evidence-pack/SKILL.md` require the schema and reject malformed specialist evidence. |
| P2 — convert mature slash commands into skills | Addressed | Canonical manual skills now exist under `.claude/skills/ship/`, `.claude/skills/audit/`, `.claude/skills/review/`, and `.claude/skills/test/`. `.claude/commands/{ship,audit,review,test}.md` are compatibility shims pointing to the skill and contract/schema files. |
| P2 — tune broad model-invocable skills | Addressed | `edge-case-audit` has a shorter model-invocable description. `fsv-verify` is a slim doctrine skill. Heavy FSV material moved to manual `fsv-verify-deep` and `fsv-verify-deep/references/adversarial-checklist.md`. Validator warns for model-invocable descriptions over 300 characters. |
| P2 — clarify `security-auditor` evidence authority | Addressed | `.claude/rules/02-agent-synergy.md` documents `security-auditor` as a no-`Bash` evidence consumer. `.claude/agents/security-auditor.md` requires output to state parent-provided versus static-inspection evidence and makes dependency-audit command ownership explicit. |
| P2 — resolve `test-writer` versus `test-engineer` overlap | Addressed | `.claude/rules/02-agent-synergy.md` declares `test-engineer` the canonical test owner and `test-writer` a deprecated read-only redirect. Validator warns if test-named agents lack test skills or explicit rationale. |
| P2 — add validator coverage for settings and schema drift | Addressed | `.claude/hooks/validate-claude-config.py` now checks settings top-level keys, protected-file deny/edit/write parity, protected-file hook registration, sandbox/network waiver presence, command-skill shims, broad model-invocable skill descriptions, synergy contract references, evidence schema references, and README inventory drift. `.claude/rules/settings-policy-waivers.yml` documents current sandbox/network waivers. |
| P3 — add local Claude Code smoke-test transcript guidance | Addressed | `.claude/skills/claude-config-audit/references/live-smoke-template.md` captures `/status`, `/agents`, `/skills`, `/hooks`, `/permissions`, and `/doctor` evidence. `.claude/skills/ship/SKILL.md` requires live smoke evidence for Claude internals changes or `NOT_RUN` with reason. |
| P3 — document project-memory curation thresholds | Addressed | `.claude/rules/02-agent-synergy.md` and `.claude/README.md` define the first-200-lines memory convention and section order. Existing project memories now include `Current operating assumptions`, `Recent validated learnings`, and `Historical notes`. Validator warns on oversized memory files without the top summary section. |

### Review checklist for this PR

- Confirm `python .claude/hooks/validate-claude-config.py` exits 0 and lists no warnings.
- Confirm `python -m compileall -q .claude/hooks` exits 0.
- Confirm negative protected-file hook samples block `.env.local` and `secrets/foo` before tool execution.
- Confirm normal file access samples, such as `src/main.py`, are not blocked by the protected-file hook.
- Interactive Claude Code smoke checks are not runnable in this non-interactive environment; use `.claude/skills/claude-config-audit/references/live-smoke-template.md` during human review if needed.
