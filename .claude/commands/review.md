---
description: Conduct a DegenExus five-axis code review with local code-reviewer and security/risk specialists when relevant
---

Use the `code-reviewer` subagent and its `code-reviewer` skill for the current diff or supplied scope. Use `.claude/rules/02-agent-synergy.md` as the single source for additional specialist routing.

Review across correctness, readability, architecture, security, and performance. Add domain specialists exactly as the synergy map requires, including security, risk, prompt, lifecycle, market-data, docs/memory, FDD, or test specialists.

Categorize findings as Critical, Important, or Suggestion and cite specific files/lines with concrete recommendations.

Final output must include: Scope reviewed; Source of Truth used; Specialists/skills invoked or skipped with reason; Evidence commands and exact results; Findings by severity; at least three edge cases considered; Memory update needed yes/no plus path; Next action owner.
