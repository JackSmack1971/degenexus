---
description: Audit DegenExus Claude Code internals and documentation consistency
---

Use `claude-config-audit`, `release-evidence-pack`, and `.claude/rules/02-agent-synergy.md`.

Workflow:

1. Run `python .claude/hooks/validate-claude-config.py`.
2. Run `python -m compileall -q .claude/hooks`.
3. Check `.claude/README.md` inventories every agent, skill, hook, and command.
4. Check memory files use `.claude/agent-memory/<agent>/MEMORY.md` for every `memory: project` agent.
5. Confirm commands and specialist routing cite `.claude/rules/02-agent-synergy.md`.
6. Recommend `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status` checks inside Claude Code when available.

Final output must include: Scope reviewed; Source of Truth used; Specialists/skills invoked; Evidence commands and exact results; Findings by severity; at least three edge cases considered; Memory update needed yes/no plus path; Next action owner.
