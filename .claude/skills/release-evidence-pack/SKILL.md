---
name: release-evidence-pack
description: >
  Assemble merge-readiness evidence for DegenExus PRs: tests, compile checks,
  security scan status, edge cases, changed files, memory updates, and gate verdicts.
---

# Release Evidence Pack

## Workflow

1. Record changed files and classify runtime, test, docs, memory, and `.claude` impacts.
2. Run or collect evidence for `python -m compileall -q src/`, targeted pytest, full pytest when feasible, and `.claude` config validation when relevant.
3. Summarize security checks, including secrets scan status and dependency audit status if dependencies changed.
4. List at least three edge cases considered.
5. State whether `memory/` files changed and why.
6. Produce a GO/NO-GO recommendation with blockers separated from recommendations.

## Output Sections

- Scope
- Commands and exact outcomes
- Specialist findings
- Edge cases
- Memory updates
- Remaining risk
- Final verdict
