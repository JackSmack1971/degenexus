---
description: Simplify DegenExus code for clarity while preserving source-of-truth behavior
---

Use existing project tests, `code-reviewer`, and `fsv-verify` rather than plugin-only simplification skills.

Workflow:

1. Identify the target code and source-of-truth behavior.
2. Read callers, tests, edge cases, and relevant invariants before editing.
3. Prefer deletion, guard clauses, extracted helpers, descriptive names, and removal of dead code after proof.
4. Apply one simplification at a time.
5. After each meaningful change, run targeted tests and compare behavior against source-of-truth expectations.
6. Run `python3 -m compileall -q src/` for runtime changes.
7. If behavior changes unexpectedly, revert that simplification and investigate.
