---
description: Break work into small verifiable DegenExus tasks with acceptance criteria and dependency ordering
---

Plan mode is read-only unless the user explicitly asks you to write plan files.

Workflow:

1. Read the request, relevant docs, and affected code/tests.
2. Identify source-of-truth locations and risk surfaces.
3. Slice work vertically into independently verifiable increments.
4. For each task, list acceptance criteria, verification commands, source-of-truth evidence, and at least three edge cases.
5. Identify which specialists should review each task.
6. Present the plan for human review before implementation.

If asked to persist the plan, write it under `tasks/` or the user-specified path.
