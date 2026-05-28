---
description: Compatibility shim for the canonical /review skill workflow
---

Invoke the project skill `/review` and follow these canonical references instead of duplicating workflow prose:

- `.claude/skills/review/SKILL.md`
- `.claude/rules/synergy-contract.yml`
- `.claude/rules/evidence-schema.yml`
- `.claude/rules/02-agent-synergy.md`

Final output must emit the minimum gate fields from `.claude/rules/evidence-schema.yml`: `verdict`, `scope_reviewed`, `source_of_truth`, and `findings`.
