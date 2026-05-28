---
description: Run the DegenExus pre-merge gate with config health, tests, specialist fan-out, and a GO/NO-GO decision
---

Use `.claude/rules/02-agent-synergy.md` for specialist routing.

Invocation model:

- For full fan-out behavior, run `claude --agent ship` so `ship` is the main-session coordinator and its `Agent(...)` tool restrictions apply.
- When invoked as `/ship` from another session, the parent session must perform specialist fan-out itself using the same synergy map; a spawned subagent cannot spawn more subagents.

Required gate evidence:

1. Validate Claude Code config with `python .claude/hooks/validate-claude-config.py` when Claude internals changed.
2. Verify `python -m compileall -q src/`.
3. Verify `python -m pytest tests/ -v` or explain a real environment limitation.
4. Verify `python -m pyflakes src/` when available.
5. Run `pip-audit -r requirements.txt` when dependencies changed or release policy requires it.
6. Confirm no `.env*`, SQLite DB, WAL, or SHM files were added.
7. Fan out to `code-reviewer`, `security-auditor`, and `test-engineer`; add domain specialists for risk, prompt, lifecycle, market-data, docs/memory, or FDD scopes per the synergy map.
8. If tests fail repeatedly or evidence conflicts, use `fdd-investigator` read-only before edits.

Final output must include: GO/NO-GO verdict; Scope reviewed; Source of Truth used; Specialists/skills invoked; Evidence commands and exact results; Findings by severity; at least three edge cases considered; blockers; recommendations; Memory update needed yes/no plus path; Next action owner.
