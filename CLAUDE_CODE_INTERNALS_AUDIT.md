# Claude Code Internals Audit — Actionable Improvement Plan

**Date:** 2026-05-28
**Scope:** `CLAUDE.md`, `.claude/README.md`, `.claude/settings.json`, `.claude/agents/`, `.claude/skills/`, `.claude/commands/`, `.claude/rules/`, `.claude/imports/`, `.claude/output-styles/`, `.claude/hooks/`, and `.claude/agent-memory/`.
**Deliverable constraint:** Recommendations only. This refresh intentionally modifies no Claude Code internals other than this audit file.

## 1. Research Baseline

This refresh used current Claude Code documentation plus local repository inspection.

### External references consulted

- Claude Code custom subagents: <https://code.claude.com/docs/en/sub-agents>
  - Applied points: project subagents live under `.claude/agents/`; subagents can preload skills with `skills:`; `memory: project` maps to `.claude/agent-memory/<agent>/`; `permissionMode: bypassPermissions` is dangerous; subagent memory loads only the first 200 lines or 25 KB of `MEMORY.md`.
- Claude Code skills: <https://code.claude.com/docs/en/skills>
  - Applied points: skills are the preferred extensibility unit for reusable procedures; `.claude/commands/` still works but skills support richer frontmatter, supporting files, direct slash invocation, model invocation, and subagent execution; skills stay in context after invocation and may be partially reattached after compaction.
- Claude Code hooks: <https://code.claude.com/docs/en/hooks>
  - Applied points: hooks are deterministic lifecycle automation; current hook events include more than the older minimal event set; project-relative hooks should use `CLAUDE_PROJECT_DIR` when possible so they work from changed working directories.
- Claude Code memory: <https://code.claude.com/docs/en/memory>
  - Applied points: `CLAUDE.md` is guidance, not enforcement; root `CLAUDE.md` is re-read after compaction; overgrown instruction files reduce adherence; strict timing/security requirements belong in hooks or permissions.
- Claude Code configuration debugging: <https://code.claude.com/docs/en/debug-your-config>
  - Applied points: `/context`, `/memory`, `/skills`, `/agents`, `/hooks`, `/permissions`, `/doctor`, and `/status` are the right live-smoke commands for confirming what actually loaded.

### Local evidence commands run

```bash
find .. -name AGENTS.md -print
find .claude -maxdepth 4 -type f -print 2>/dev/null | sort | sed -n '1,240p'
python .claude/hooks/validate-claude-config.py
python -m compileall -q .claude/hooks
python - <<'PY'
from pathlib import Path
import yaml
print('CLAUDE.md lines', len(Path('CLAUDE.md').read_text().splitlines()))
print('audit lines', len(Path('CLAUDE_CODE_INTERNALS_AUDIT.md').read_text().splitlines()))
print('\nAgents:')
for p in sorted(Path('.claude/agents').glob('*.md')):
    text = p.read_text()
    fm = yaml.safe_load(text.split('---', 2)[1]) or {}
    print(p.name, fm)
print('\nSkills:')
for p in sorted(Path('.claude/skills').glob('*/SKILL.md')):
    text = p.read_text()
    fm = yaml.safe_load(text.split('---', 2)[1]) or {}
    print(p.parent.name, fm, 'lines', len(text.splitlines()))
print('\nCommands:')
for p in sorted(Path('.claude/commands').glob('*.md')):
    print(p.name, len(p.read_text().splitlines()))
PY
wc -l .claude/agent-memory/*/MEMORY.md | sort -n
cat .claude/settings.json
cat .claude/rules/synergy-contract.yml
cat .claude/rules/evidence-schema.yml
```

### Local validation result

- `python .claude/hooks/validate-claude-config.py` returned `claude config validation ok` and listed the model-invocable skills.
- `python -m compileall -q .claude/hooks` passed with no output.
- `CLAUDE.md` is 101 lines, comfortably below the documentation warning threshold where instruction adherence can degrade.
- Every checked-in `memory: project` subagent has a corresponding `.claude/agent-memory/<agent>/MEMORY.md` file.
- All agent memory files are currently small: 25-30 lines each, well under the documented first-200-lines startup load limit.

## 2. Executive Summary

The current Claude Code internals are materially stronger than the stale findings this file previously carried. The setup now has:

- A machine-readable routing contract at `.claude/rules/synergy-contract.yml`.
- A schema file for routed evidence at `.claude/rules/evidence-schema.yml`.
- Command shims for `/audit`, `/review`, `/ship`, and `/test` that delegate to canonical skills.
- A protected-file `PreToolUse` hook plus explicit deny rules for secrets and SQLite runtime files.
- Project memory directories for all active `memory: project` agents.
- A validator that checks frontmatter, skill references, project memory naming, command shims, settings policy, hook scripts, README drift, and broad security posture.

The next improvements should therefore be evolutionary rather than a redesign. The highest-value work is to keep the current synergy model but make it more resilient to Claude Code platform drift, working-directory changes, live-session drift, and duplicated workflow logic.

## 3. Stale Findings Removed

The following older findings are no longer valid and should not guide future work:

1. **“Project subagent memory is missing.”** No longer true. All active `memory: project` agents have uppercase `MEMORY.md` files, and the validator enforces this.
2. **“Settings do not protect `.env` writes or edits.”** No longer true. `Read`, `Edit`, and `Write` deny rules cover `.env*`, credential material, and SQLite runtime files.
3. **“There is no `PreToolUse` protected-file guard.”** No longer true. `.claude/settings.json` wires `protect-sensitive-files.py` to `PreToolUse` for read, write, edit, multiedit, and bash operations.
4. **“Slash commands duplicate the canonical workflows.”** Partly stale. `/audit`, `/review`, `/ship`, and `/test` are now compatibility shims to skills. Remaining direct commands still exist for `/build`, `/code-simplify`, `/plan`, and `/spec`.
5. **“Routing is only prose.”** No longer true. `.claude/rules/synergy-contract.yml` is now the machine-readable routing source of truth, with `.claude/rules/02-agent-synergy.md` as the companion human-readable reference.
6. **“There is no evidence schema.”** No longer true. `.claude/rules/evidence-schema.yml` defines required gate fields and routed specialist evidence structure.

## 4. Current Inventory Snapshot

### 4.1 Instruction layer

- `CLAUDE.md` is concise at 101 lines and mostly delegates operational detail to skills, rules, and `.claude/README.md`.
- `.claude/README.md` is the broad inventory and maps agents, skills, commands, hooks, rules, memory conventions, and naming rules.
- `.claude/imports/doctrine-summary.md` and `.claude/rules/01-security.md` keep security and doctrine separate from the root instruction file.

### 4.2 Agents

Active specialist set:

| Agent | Primary role | Write access | Preloaded skills | Memory |
| --- | --- | ---: | --- | --- |
| `code-reviewer` | Five-dimension code review | No | `code-reviewer` | Project |
| `docs-memory-curator` | Claude internals, docs, memory consistency | No | `claude-config-audit`, `release-evidence-pack` | Project |
| `fdd-investigator` | Root-cause analysis and falsification | No | `forensic-debug`, `fsv-verify` | Project |
| `market-data-integrity-auditor` | OHLCV, indicators, fallbacks, NaN/warmup behavior | No | `edge-case-audit`, `fsv-verify` | Project |
| `prompt-injection-auditor` | Prompt-safety and trust-boundary review | No | `prompt-safety-review`, `edge-case-audit` | Project |
| `risk-gate-verifier` | Risk and execution gate verification | No | `risk-control-audit`, `edge-case-audit`, `fsv-verify` | Project |
| `security-auditor` | Security, secrets, dependency handoffs, prompt escalation | No | `security-review`, `prompt-safety-review`, `claude-config-audit` | Project |
| `ship` | Merge-readiness orchestration | No direct writes | `claude-config-audit`, `release-evidence-pack` | Project |
| `test-engineer` | Canonical test author and coverage specialist | Yes | `test-regression`, `edge-case-audit`, `fsv-verify` | Project |
| `test-writer` | Deprecated read-only compatibility alias | No | None | No project memory field |
| `trade-lifecycle-auditor` | SQLite and trade lifecycle source-of-truth verification | No | `sqlite-sot-verify`, `fsv-verify`, `edge-case-audit` | Project |

### 4.3 Skills and commands

- Workflow skills with command-shim coverage: `audit`, `review`, `ship`, `test`.
- Model-invocable specialist skills: `code-reviewer`, `edge-case-audit`, `forensic-debug`, `fsv-verify`, `prompt-safety-review`, `risk-control-audit`, `security-review`, `sqlite-sot-verify`, `test-regression`.
- Manual-only or preloaded support skills: `claude-config-audit`, `dependency-audit`, `fsv-verify-deep`, `release-evidence-pack`, `run-degenexus`.
- Remaining direct commands: `/build`, `/code-simplify`, `/plan`, `/spec`.

### 4.4 Hooks and safety controls

Configured hooks:

| Hook event | Script | Current purpose |
| --- | --- | --- |
| `PreToolUse` | `protect-sensitive-files.py` | Block protected file access before read/write/edit/bash tool execution. |
| `PostToolUse` | `validate-claude-config.py` | Validate Claude config after writes/edits/multiedits. |
| `SubagentStart` / `SubagentStop` | `log-subagent-event.py` | Record local JSONL subagent lifecycle events. |
| `ConfigChange` | `validate-claude-config.py` | Validate on project settings and skill config changes. |
| `SessionStart` | `session-start-reminder.py` | Print project routing reminder. |
| `FileChanged` | `warn-env-file-changed.py` | Warn when `.env*`-style files change. |

## 5. Priority Action Register

### P0 — Keep validator aligned with current Claude Code hook events

**Finding:** The local validator has a fixed `ALLOWED_HOOK_EVENTS` list. Current Claude Code hook documentation includes a broader lifecycle than the validator allows, including events such as `Setup`, `UserPromptExpansion`, `PermissionRequest`, `PermissionDenied`, `PostToolUseFailure`, `PostToolBatch`, `TaskCreated`, `TeammateIdle`, `PreCompact`, `PostCompact`, `WorktreeCreate`, `WorktreeRemove`, `InstructionsLoaded`, `CwdChanged`, and `MessageDisplay`. The current repository settings do not use those events, so validation passes today, but the validator may block valid future configuration.

**Why it matters:** The `.claude` system is now mature enough that future improvements are likely to use additional hooks. A stale allow-list will create false negatives and encourage bypassing validation.

**Actionable improvement:**

1. Add every documented hook event to `ALLOWED_HOOK_EVENTS` in `.claude/hooks/validate-claude-config.py`.
2. Split hook metadata into `matcher_allowed`, `matcher_ignored`, and `decision_capable` maps instead of two small sets.
3. Add a short `HOOK_EVENT_SOURCE_DATE = "2026-05-28"` comment and a reference to <https://code.claude.com/docs/en/hooks>.
4. Add a small validator self-test fixture or script that validates one representative config containing newer events without changing project settings.

**Acceptance criteria:**

- `python .claude/hooks/validate-claude-config.py` still passes.
- `python -m compileall -q .claude/hooks` still passes.
- A scratch config containing `InstructionsLoaded`, `PreCompact`, and `PostToolUseFailure` is accepted by the validator logic.

### P0 — Make hook commands working-directory independent

**Finding:** Hook commands in `.claude/settings.json` call scripts using relative paths such as `python .claude/hooks/validate-claude-config.py`. Claude Code documentation recommends `CLAUDE_PROJECT_DIR` for project-stored hook scripts so hooks still work when Claude's current directory changes.

**Why it matters:** This repo has path-sensitive rules and a `CwdChanged` hook opportunity. A subagent or future workflow operating from a nested directory could make relative hook commands brittle.

**Actionable improvement:**

1. Change hook commands from `python .claude/hooks/<script>.py` to `python "$CLAUDE_PROJECT_DIR/.claude/hooks/<script>.py"` or a shell-safe equivalent.
2. Update `validate-claude-config.py` to continue resolving `ROOT` from its own location, not from process CWD.
3. Add a validation smoke command: `cd src && python ../.claude/hooks/validate-claude-config.py`.

**Acceptance criteria:**

- Hooks still validate from repository root.
- The validator passes when launched from `src/`.
- The settings validator accepts the new command strings.

### P1 — Add `InstructionsLoaded` and optional `CwdChanged` observability

**Finding:** Debug documentation explicitly calls out `/memory`, `/context`, and the `InstructionsLoaded` hook as ways to confirm what instruction files actually loaded. The current setup has `SessionStart` reminders and config validation, but no durable log of loaded instruction files.

**Why it matters:** The repository depends on multiple instruction sources: `AGENTS.md`, `CLAUDE.md`, `.claude/rules/*`, agent frontmatter, skill frontmatter, and project memories. Debugging future “Claude ignored the rule” reports would be easier with a local, redacted log of instruction-load events.

**Actionable improvement:**

1. Add `.claude/hooks/log-instructions-loaded.py` that writes redacted event summaries to `.claude/local/instructions-loaded.jsonl`.
2. Register it under `InstructionsLoaded` once the validator allow-list is updated.
3. Optionally add a `CwdChanged` hook that prints a short reminder that project hooks should continue to rely on `CLAUDE_PROJECT_DIR`.
4. Ensure `.claude/local/` remains ignored and never committed.

**Acceptance criteria:**

- `/memory` and `/context` live smoke output can be correlated with `.claude/local/instructions-loaded.jsonl`.
- No secret or full prompt content is written to the log.
- `python -m compileall -q .claude/hooks` passes.

### P1 — Convert remaining direct slash commands into skill-backed workflows or declare them intentionally simple

**Finding:** `/audit`, `/review`, `/ship`, and `/test` have been modernized into skill shims, but `/build`, `/code-simplify`, `/plan`, and `/spec` still keep full workflow prose in `.claude/commands/`. Claude Code skills now provide the same slash-command affordance while adding supporting files and richer frontmatter.

**Why it matters:** The command layer is now mixed: some commands delegate to canonical skills and others are standalone. That is not broken, but it raises drift risk as conventions evolve.

**Actionable improvement:**

1. Create `.claude/skills/build/SKILL.md`, `.claude/skills/code-simplify/SKILL.md`, `.claude/skills/plan/SKILL.md`, and `.claude/skills/spec/SKILL.md` if these workflows are expected to grow.
2. Replace the corresponding command files with shims that cite the skill, `.claude/rules/synergy-contract.yml`, and `.claude/rules/evidence-schema.yml`.
3. If a workflow should remain command-only, add a one-line `Intentional command-only because ...` note to the command file and README command matrix.

**Acceptance criteria:**

- All user-facing slash workflows have one canonical source.
- `validate-claude-config.py` verifies either a skill shim or an intentional exception for every command.
- README command matrix remains in sync.

### P1 — Strengthen live-smoke evidence for Claude Code internals changes

**Finding:** The current `claude-config-audit` skill includes a live smoke template reference, and `/ship` requires live smoke only for internals changes when an interactive Claude Code environment is available. The file-level validation is strong, but live smoke remains mostly manual.

**Why it matters:** Static validation cannot prove Claude Code actually loaded project skills, agents, hooks, permissions, and memories in the active session. The docs recommend `/context`, `/skills`, `/agents`, `/hooks`, `/permissions`, `/doctor`, and `/status` for this exact problem.

**Actionable improvement:**

1. Expand `.claude/skills/claude-config-audit/references/live-smoke-template.md` into a checklist with explicit PASS/WARNING/NOT_RUN fields for `/context`, `/memory`, `/skills`, `/agents`, `/hooks`, `/permissions`, `/doctor`, and `/status`.
2. Require the checklist in `release-evidence-pack` when `.claude/**`, `CLAUDE.md`, or `AGENTS.md` changed.
3. Add a section for “expected loaded objects” generated from the local inventory: active agents, model-invocable skills, manual-only skills, hooks, and project memory roots.

**Acceptance criteria:**

- An internals PR cannot claim full live validation without enumerating the relevant Claude Code live-smoke commands.
- Non-interactive sessions can still mark those commands `NOT_RUN` with an environment reason.

### P2 — Add schema validation for actual specialist outputs, not just config files

**Finding:** `.claude/rules/evidence-schema.yml` defines required fields, and agent prompts require them, but no hook or script currently validates a captured specialist result against the schema.

**Why it matters:** The strongest synergy goal is reliable handoff evidence. A schema file is useful only if `/ship`, `/review`, or a supporting script can reject missing `verdict`, `scope_reviewed`, `source_of_truth`, or `findings` before a release decision.

**Actionable improvement:**

1. Add `.claude/hooks/validate-evidence-payload.py` or `.claude/scripts/validate-evidence-payload.py` that reads JSON/YAML/Markdown-with-frontmatter evidence and checks `.claude/rules/evidence-schema.yml`.
2. Update `release-evidence-pack` to ask specialists to emit a fenced `yaml` block matching the schema.
3. Teach `/ship` to collect those blocks and run the validator when shell execution is available.

**Acceptance criteria:**

- Missing `verdict` or empty `source_of_truth.files` fails the evidence validator.
- `NEEDS_INFO` is allowed only with a concrete remediation owner or handoff.
- `/ship` reports schema validation as PASS/WARNING/FAIL.

### P2 — Add explicit read-only enforcement tests for read-only agents

**Finding:** Most agents are read-only by frontmatter and disallow `Write`, `Edit`, and often `Bash`. The validator permits only `test-engineer` as a known write-capable agent, but there is no dedicated regression fixture documenting the allowed/blocked matrix.

**Why it matters:** The read-only/write-capable distinction is a core safety boundary for agent synergy. A future agent addition or tool-name change should not silently weaken it.

**Actionable improvement:**

1. Add a validator check that every agent except `test-engineer` and explicitly approved orchestrators disallows `Write`, `Edit`, and `MultiEdit`.
2. Require any write-capable agent to have `permissionMode: acceptEdits` or stricter, never `bypassPermissions`.
3. Add a README section named “Write-capable exception register” that currently lists only `test-engineer`.

**Acceptance criteria:**

- Adding `Write` to `security-auditor` causes validation failure.
- Adding `bypassPermissions` anywhere causes validation failure.
- The exception register and validator constant remain in sync.

### P2 — Tune broad model-invocable skills to avoid accidental context bloat

**Finding:** `edge-case-audit` and `fsv-verify` are valuable and intentionally model-invocable, but their descriptions are broad. Claude Code documentation notes that invoked skills remain in context and are reattached after compaction within budget.

**Why it matters:** Broad skills can trigger often and then persist in context, which may reduce room for source code, test output, or specialist findings. The current descriptions are under the validator's 300-character limit, but trigger breadth is still a qualitative risk.

**Actionable improvement:**

1. Split `fsv-verify` into a tiny always-invocable doctrine skill and keep `fsv-verify-deep` manual-only for the expensive checklist.
2. Narrow `edge-case-audit` trigger wording to safety-critical, resilience, and boundary reviews rather than generic “edge cases” if accidental invocation is observed.
3. Add a short “context cost” note to `.claude/README.md` explaining which skills are safe to preload and which should stay manual.

**Acceptance criteria:**

- Model-invocable descriptions remain concise.
- Heavy reference material stays in `references/` and is loaded only on demand.
- `/skills` live smoke confirms expected visibility.

### P2 — Introduce a generated inventory check to reduce README drift

**Finding:** The validator already checks README drift in broad terms, but the inventory is still manually maintained. The local `.claude` tree is structured enough to generate an agent/skill/command/hook summary.

**Why it matters:** The README is useful because it is comprehensive. Manual updates become harder as agents, skills, and hooks grow.

**Actionable improvement:**

1. Add a `--print-inventory` mode to `validate-claude-config.py` that emits Markdown tables for agents, skills, commands, hooks, and memories.
2. Add a generated block marker in `.claude/README.md`, such as `<!-- BEGIN GENERATED CLAUDE INVENTORY -->`.
3. Validate that the generated block matches the file.

**Acceptance criteria:**

- Adding a skill without updating README fails validation or prints an exact patch block.
- The generated inventory includes invocation mode, owner agents, and memory status.

## 6. Suggested Implementation Sequence

1. **Validator platform refresh:** Update hook event allow-list and matcher metadata first, because it unblocks safe use of newer hooks.
2. **Hook path hardening:** Switch hook commands to `CLAUDE_PROJECT_DIR` and smoke-test from a nested directory.
3. **Instruction observability:** Add `InstructionsLoaded` logging once the validator accepts the event.
4. **Command canonicalization:** Decide whether `/build`, `/code-simplify`, `/plan`, and `/spec` should become skills or explicitly documented command-only workflows.
5. **Evidence enforcement:** Add a payload validator and teach `/ship` to require schema-valid specialist blocks.
6. **README inventory generation:** Automate drift checks after the final structure settles.

## 7. Verification Checklist for the Next Internals PR

Use this checklist when implementing any of the recommendations above:

```markdown
## Claude Internals Verification

### Static validation
- [ ] `python .claude/hooks/validate-claude-config.py`
- [ ] `python -m compileall -q .claude/hooks`
- [ ] `cd src && python ../.claude/hooks/validate-claude-config.py`

### Inventory checks
- [ ] Every `memory: project` agent has `.claude/agent-memory/<agent>/MEMORY.md`.
- [ ] Every preloaded skill in agent frontmatter exists under `.claude/skills/<skill>/SKILL.md`.
- [ ] Every workflow command either delegates to a skill or declares why it is command-only.
- [ ] `.claude/README.md` inventory matches agents, skills, commands, hooks, and rules.

### Safety checks
- [ ] No `.env*`, `secrets/**`, `*.pem`, `*.key`, `*.db`, `*.db-wal`, or `*.db-shm` files are added.
- [ ] No agent uses `permissionMode: bypassPermissions`.
- [ ] Only documented write-capable agents can use `Write`, `Edit`, or `MultiEdit`.
- [ ] Hook commands work from a nested CWD.

### Live smoke, if interactive Claude Code is available
- [ ] `/context` shows expected memory, skills, tools, and instruction sources.
- [ ] `/memory` lists project `CLAUDE.md` and expected rules.
- [ ] `/skills` lists project skills and expected invocation modes.
- [ ] `/agents` lists all project agents with expected settings.
- [ ] `/hooks` lists project hooks.
- [ ] `/permissions` shows protected-file deny rules.
- [ ] `/doctor` reports no config/schema issues.
- [ ] `/status` shows expected settings sources.
```

## 8. Bottom Line

The Claude Code internals are currently coherent, validated, and substantially aligned with the 2026 Claude Code feature set. The main remaining risks are not missing pieces; they are **platform-drift risk**, **relative-path hook brittleness**, **manual live-smoke gaps**, and **unenforced evidence shape at handoff time**. Addressing the P0 and P1 items above should make the agent/skill ecosystem more robust without changing the successful routing architecture already in place.
