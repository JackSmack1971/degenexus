---
description: Run the DegenExus pre-merge gate with config health, tests, specialist fan-out, and a GO/NO-GO decision
---

Use the `ship` subagent as the central orchestrator for the current diff or supplied scope.

Required gate evidence:

1. Validate Claude Code config with `python .claude/hooks/validate-claude-config.py` when Claude internals changed.
2. Verify `python3 -m compileall -q src/`.
3. Verify `python3 -m pytest tests/ -v` or explain a real environment limitation.
4. Verify `python3 -m pyflakes src/` when available.
5. Confirm no `.env*`, SQLite DB, WAL, or SHM files were added.
6. Fan out to `code-reviewer`, `security-auditor`, and `test-engineer`; add domain specialists for risk, prompt, lifecycle, market-data, and docs/memory scopes.
7. If tests fail, use `fdd-investigator` read-only before edits.

Final output must include a GO/NO-GO verdict, specialist findings, exact command evidence, at least three edge cases considered, blockers, recommendations, and memory-update status.
