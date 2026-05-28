---
description: Break work into small verifiable DegenExus tasks with acceptance criteria and dependency ordering
---

Plan mode is read-only unless the user explicitly asks you to write plan files. Use `.claude/rules/02-agent-synergy.md` to map risk surfaces to specialists.

Workflow:

1. Read the request, relevant docs, and affected code/tests.
2. Identify source-of-truth locations and risk surfaces.
3. Slice work vertically into independently verifiable increments.
4. For each task, list acceptance criteria, verification commands, source-of-truth evidence, and at least three edge cases.
5. Identify which specialists should review each task.
6. Present the plan for human review before implementation.

If asked to persist the plan, write it under `tasks/` or the user-specified path.

Final output must include: Scope reviewed; Source of Truth used; Specialists/skills planned; Evidence commands to run; Findings/risks by severity; at least three edge cases considered; Memory update needed yes/no plus path; Next action owner.
