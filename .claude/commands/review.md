---
description: Conduct a DegenExus five-axis code review with local code-reviewer and security/risk specialists when relevant
---

Use the `code-reviewer` subagent and its `code-reviewer` skill for the current diff or supplied scope.

Review across correctness, readability, architecture, security, and performance. Add these specialists when the scope requires them:

- `security-auditor` for auth, secrets, dependencies, prompt safety, or untrusted input.
- `risk-gate-verifier` for risk gates, execution gates, trade proposals, exposure, or position sizing.
- `prompt-injection-auditor` for prompt construction or cross-agent text flow.
- `trade-lifecycle-auditor` for state transitions or SQLite persistence.
- `market-data-integrity-auditor` for yfinance, OHLCV, indicators, fallback data, or network degradation.

Categorize findings as Critical, Important, or Suggestion and cite specific files/lines with concrete recommendations.
