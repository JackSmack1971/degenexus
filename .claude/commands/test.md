---
description: Compatibility shim for the canonical /test skill workflow
---

Invoke the project skill `/test` and follow these canonical references instead of duplicating workflow prose:

- `.claude/skills/test/SKILL.md`
- `.claude/rules/synergy-contract.yml`
- `.claude/rules/evidence-schema.yml`
- `.claude/rules/02-agent-synergy.md`

Final output must emit the minimum gate fields from `.claude/rules/evidence-schema.yml`: `verdict`, `scope_reviewed`, `source_of_truth`, and `findings`.
