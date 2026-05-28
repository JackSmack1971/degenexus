# Claude Code Live Smoke Evidence

Use this checklist when `.claude/**`, `CLAUDE.md`, or `AGENTS.md` changed. In non-interactive environments, mark each live command `NOT_RUN` and give the environment reason.

Date:
Claude Code version:
Working directory:
Changed internals files:
Environment: interactive Claude Code / non-interactive agent / other

## Expected Loaded Objects

Populate from `python .claude/hooks/validate-claude-config.py --print-inventory` or the generated block in `.claude/README.md`.

- Active agents:
- Model-invocable skills:
- Manual-only skills:
- Hooks:
- Project memory roots:
- Protected permission deny patterns:

## Live Commands

| Command | Status (`PASS`/`WARNING`/`NOT_RUN`) | Evidence summary | Follow-up |
| --- | --- | --- | --- |
| `/context` |  | Expected memory, skills, tools, and instruction sources are present. |  |
| `/memory` |  | Project `CLAUDE.md`, AGENTS.md context, and expected rules/memories are visible. |  |
| `/skills` |  | Project skills and invocation modes match README inventory. |  |
| `/agents` |  | Project agents match README inventory and write-capable exception register. |  |
| `/hooks` |  | Registered hooks match `.claude/settings.json`. |  |
| `/permissions` |  | Protected-file deny rules are visible. |  |
| `/doctor` |  | No config/schema issues, or warnings are explained. |  |
| `/status` |  | Expected settings sources and project directory are active. |  |

## Static Companion Checks

| Command | Status (`PASS`/`FAIL`/`WARNING`/`NOT_RUN`) | Output or reason |
| --- | --- | --- |
| `python .claude/hooks/validate-claude-config.py` |  |  |
| `python .claude/hooks/validate-claude-config.py --self-test` |  |  |
| `python -m compileall -q .claude/hooks` |  |  |
| `cd src && python ../.claude/hooks/validate-claude-config.py` |  |  |

## Findings

- Blockers:
- Warnings:
- Follow-up issues:
