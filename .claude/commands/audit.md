---
description: Audit Claude Code internals and DegenExus project gates before review or ship
---

Use the `claude-config-audit` and `release-evidence-pack` skills.

Required checks:

1. Run `python .claude/hooks/validate-claude-config.py`.
2. Run `python -m compileall -q .claude/hooks`.
3. Inventory agents, skills, commands, rules, imports, output styles, and memory.
4. Report missing skill references, invalid frontmatter, stale command references, broad permissions, and hook gaps.
5. Recommend `/context`, `/memory`, `/agents`, `/skills`, `/hooks`, `/permissions`, `/doctor`, and `/status` checks inside Claude Code when available.
