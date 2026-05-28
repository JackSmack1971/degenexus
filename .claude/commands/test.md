---
description: Run DegenExus pytest workflow with Prove-It regressions, FSV-AAA assertions, and edge-case coverage
---

Use the `test-engineer` subagent and `test-regression`, `edge-case-audit`, and `fsv-verify` skills for test authoring or coverage analysis.

For new behavior:
1. Identify the source of truth and current test patterns.
2. Write pytest coverage with FSV-AAA structure: PRE source-of-truth read, one ACT, POST reread and expected DIFF assertion.
3. Include BVA/ECP cases for empty/zero, min/max boundary, malformed/adversarial input, and concurrency/ordering when applicable.
4. Use `pytest-mock`'s `mocker` fixture; do not import `unittest.mock` directly.
5. Mock LLM providers, yfinance/network calls, time, and random behavior.
6. Run targeted pytest first, then broader regression tests when feasible.

For bugs, use Prove-It: write a failing regression test first, confirm it fails, then fix and confirm it passes.

Final output must include: Scope reviewed; Source of Truth used; Specialists/skills invoked; Evidence commands and exact results; Findings by severity or coverage gap; at least three edge cases considered; Memory update needed yes/no plus path; Next action owner.
