# DECISIONS

## ADR-009 — Make risk_decision_ttl_seconds env-configurable via RISK_DECISION_TTL_SECONDS (codex/issue-139)

**Date:** 2026-05-29
**Issue:** #139
**Context:** `RiskLimits.risk_decision_ttl_seconds` (default 300 s) controls the `ExecutionGate` approval window. `from_env()` read 6 other limits from env vars but silently omitted `risk_decision_ttl_seconds`, making it impossible to tune without source edits. All other limits were already env-configurable.
**Decision:** Add `risk_decision_ttl_seconds=int(os.getenv("RISK_DECISION_TTL_SECONDS", "300")),` to `from_env()`. Default preserved at 300 s; operators can now override via env.
**Alternatives rejected:** No change (leaves operational gap); field rename (breaks API).
**Edge cases covered:** env override (42 s), env unset (300 s default).

---

## ADR-010a — Delete HardRuleViolation dead code; preserve return-value API (codex/issue-140)

**Date:** 2026-05-29
**Issue:** #140
**Context:** `HardRuleViolation(Exception)` existed in `risk_gate.py` with docstring "Raised when a trade proposal violates a hard risk rule." but `check_hard_rules()` returns `list[str]` and never raises. The class occupied 7 lines and created a permanently uncovered code path (lines 24-26 at 0%).
**Decision:** Delete the class and its `__init__.py` export. The return-value API is the correct and established contract; no callers depend on the exception.
**Alternatives rejected:** Raising `HardRuleViolation` from `check_hard_rules()` is an API-breaking change; leaving the dead class perpetuates a misleading contract for future contributors.
**Edge cases covered:** `grep -rn "HardRuleViolation" src/ tests/` returns 0 results; all 419 tests continue to pass.

---

## ADR-010c — Remove stale langchain mypy overrides after dependency removal (codex/issue-138)

**Date:** 2026-05-29
**Issue:** #138
**Context:** PR #123 removed `langchain` and `langchain-anthropic` from `requirements.txt`. The `[[tool.mypy.overrides]]` block in `pyproject.toml` was not updated, leaving `ignore_missing_imports = true` for packages no longer in the project.
**Decision:** Remove `"langchain"`, `"langchain.*"`, `"langchain_anthropic"`, `"langchain_anthropic.*"` from the override list. Active override modules remain: `ta`, `ta.*`, `yfinance`, `yfinance.*`, `anthropic`, `openai`, `openai.*`.
**Alternatives rejected:** Keeping the stale entries (would silently suppress errors if langchain were re-added without type stubs).
**Edge cases covered:** `grep "langchain" pyproject.toml requirements.txt src/` returns 0; mypy still passes with 35 source files.

---

## ADR-010e — Create .github/PULL_REQUEST_TEMPLATE/ referenced by AGENTS.md (codex/issue-142)

**Date:** 2026-05-29
**Issue:** #142
**Context:** AGENTS.md instructed contributors to use `.github/PULL_REQUEST_TEMPLATE/default.md` or `bug-fix.md`. Neither file nor the directory existed. Without templates, GitHub shows a blank PR body and contributors receive no automatic reminder of the FSV evidence checklist required by CLAUDE.md.
**Decision:** Create both template files. `default.md` for standard PRs (summary, FDD evidence, PRE/POST FSV state, 3 edge cases, memory updates). `bug-fix.md` for bug-specific PRs (trigger, root cause, reproduction evidence, regression proof).
**Alternatives rejected:** Removing the AGENTS.md reference (loses enforcement surface for FSV requirements at PR creation time).
**Edge cases covered:** `ls .github/PULL_REQUEST_TEMPLATE/` → both files exist; AGENTS.md reference is now resolvable.

---

## ADR-010d — Correct README Good First Contributions module paths (codex/issue-141)

**Date:** 2026-05-29
**Issue:** #141
**Context:** README.md listed `src/indicators.py`, `src/performance.py`, `src/context_injector.py` as good-first-contribution targets. These root-level paths don't exist; the actual files are `src/data/indicators.py`, `src/memory/performance.py`, `src/memory/context_injector.py`.
**Decision:** Correct all three paths in README.md line 160 to match actual filesystem layout.
**Alternatives rejected:** No change (contributors cannot find files); adding root-level symlinks (unnecessary complexity).
**Edge cases covered:** `find src/ -name "indicators.py" -o -name "performance.py" -o -name "context_injector.py"` confirms correct sub-package locations.

---

## ADR-010b — Synchronize AGENTS.md coverage gate with CI enforcement (codex/issue-137)

**Date:** 2026-05-29
**Issue:** #137
**Context:** PR #125 raised `--cov-fail-under` from 50 to 90 in CI. AGENTS.md was not updated in that PR, leaving contributors with stale documentation stating 50% is acceptable.
**Decision:** Update AGENTS.md line 20 to state `--cov-fail-under=90` and remove the parenthetical about "CLAUDE.md sets the stronger target" since CI now directly enforces 90%.
**Alternatives rejected:** No change (perpetuates contributor confusion); reducing CI threshold to 50 (would weaken the quality gate that was intentionally raised).
**Edge cases covered:** `grep "cov-fail-under" AGENTS.md ci.yml` shows consistent 90%.

---

## ADR-009 — Keep risk hard-rule API return-value based and make TTL env-configurable

**Date:** 2026-05-29
**Issues:** #139, #140
**Context:** `RiskGate.check_hard_rules()` already exposes hard-rule failures as `list[str]` and downstream code builds `RiskDecision` objects from that return value. A dead `HardRuleViolation` exception implied an exception-based contract while never being raised. Separately, `RiskLimits.risk_decision_ttl_seconds` existed but `RiskLimits.from_env()` did not read `RISK_DECISION_TTL_SECONDS`.
**Decision:** Preserve the established return-value API by deleting `HardRuleViolation` and its export, and add `RISK_DECISION_TTL_SECONDS` to `RiskLimits.from_env()` with regression coverage for env override and default behavior.
**Alternatives rejected:** Raising `HardRuleViolation` from `check_hard_rules()` would be an API-breaking change across orchestrator/risk tests; leaving the class in place perpetuates misleading dead code.
**Edge cases covered:** env override (`42` seconds), unset env default (`300` seconds), existing hard-rule return-value tests unchanged.

## ADR-010 — Contributor governance docs must point to physical templates and current gates

**Date:** 2026-05-29
**Issues:** #137, #138, #141, #142
**Context:** AGENTS.md and README are contributor-facing SoT. They referenced a 50% coverage threshold, phantom PR templates, and non-existent module paths; `pyproject.toml` retained mypy waivers for dependencies removed from requirements.
**Decision:** Update docs/config to match physical repository state: CI coverage gate is 90%, README good-first paths include their package directories, stale langchain mypy waivers are removed, and both referenced PR templates now exist with FDD/FSV evidence fields.
**Alternatives rejected:** Removing the PR-template reference would avoid the phantom-path bug but lose a useful governance enforcement surface; retaining removed dependency waivers would weaken future type-check gate evidence.
**Edge cases covered:** template directory existence, no stale langchain references, no stale README root-level module paths, AGENTS threshold matches CI.

## ADR-001 — sys.modules injection as primary CI fix for ta-dependent tests (codex/issue-66)

**Date:** 2026-05-27
**Issue:** #66
**Context:** `ta>=0.11.0` fails to build wheels in some environments (setuptools>=65 removes `install_layout`). 11 tests used dotted-path `patch("ta.volatility.BollingerBands", ...)` which requires ta to be importable at patch-time — these tests fail with `ModuleNotFoundError` when ta is not installed. A `setuptools<65` pin was initially added but caused CI `pip-audit` to flag CVEs in old setuptools, creating a new CI failure.
**Decision:** The primary fix is **sys.modules injection** only — no `setuptools<65` pin in requirements.txt. Tests work regardless of whether ta is installed. `setuptools<65` was removed after it caused pip-audit failures in CI (pip cache miss forced fresh install, pip-audit flagged setuptools 64.x CVEs).
**Alternatives rejected:**
- Keep `setuptools<65` pin — causes pip-audit CI failures
- Replace `ta` with `pandas-ta` — requires rewriting `IndicatorEngine`
- Remove `ta` entirely — requires rewriting `IndicatorEngine`
**Edge cases covered:** BVA — empty bars, bars exactly at 30 boundary, all indicators None; ECP — ta missing, ta installed, ta raises.

---

## ADR-002 — sys.modules injection pattern for test isolation from uninstalled packages (codex/issue-66)

**Date:** 2026-05-27
**Issue:** #66
**Context:** Tests that patch dotted-path strings (`"ta.volatility.BollingerBands"`) require the package to be importable even for mock tests. This creates a hard build dependency for tests.
**Decision:** Replace all dotted-path string patches on `ta` sub-modules with `patch.dict(sys.modules, {...})` injection via the `_ta_patch()` helper. This makes tests independent of whether `ta` is installed.
**Pattern:** `_ta_patch(vol=fake_vol)` → temporarily replaces `sys.modules["ta"]` and `sys.modules["ta.volatility"]` for the duration of the `with` block.
**Applies to:** Any test for code that does `import some.package` where that package may not be available in all environments.

---

## ADR-003 — assert narrowing for Optional→required post-gate type in ExecutionAgent (codex/issue-68)

**Date:** 2026-05-27
**Issue:** #68
**Context:** `execute()` accepts `risk_decision: Optional[RiskDecision]`, passes it to `gate.validate()` which raises on None/rejected, but mypy still sees Optional reaching `_apply_conditions(proposal, risk_decision: RiskDecision)`.
**Decision:** Add `assert risk_decision is not None` after `gate.validate()` to narrow the type from Optional to RiskDecision. This satisfies mypy without changing the runtime contract.
**Alternative rejected:** Change `execute()` signature to `risk_decision: RiskDecision` — breaks callers that pass None for dry-run scenarios.

---

## ADR-004 — Explicit Direction() constructor call for str→Direction in data_analyst (codex/issue-68)

**Date:** 2026-05-27
**Issue:** #68
**Context:** `data_analyst.py:119` passes `str(...)` to `direction=` field of `MarketSignal`, which has type `Direction`. Pydantic's validator coerces it at runtime, but mypy rejects the contract.
**Decision:** Wrap with `Direction(str(response.get("direction", "LONG")).upper())` to make the coercion explicit and satisfy mypy. If the string is invalid, the `except Exception` in `_parse_signal` catches it and returns None (correct behavior).

---

## ADR-005 — DI injection for DataAnalystAgent.feed and .engine (codex/issue-69)

**Date:** 2026-05-27
**Issue:** #69
**Context:** `DataAnalystAgent.__init__` hard-instantiates `MarketFeed` and `IndicatorEngine`, making `analyze()` and `_build_bar_summary()` untestable in isolation. Existing tests use `__new__` workaround and cannot call `analyze()`.
**Decision:** Add `feed: Optional[MarketFeed] = None` and `engine: Optional[IndicatorEngine] = None` as keyword-only constructor params. Use `self.feed = feed or MarketFeed(alpha_vantage_key=None)` pattern (same as resolved issue #57 for PortfolioManagerAgent).
**Coverage gain:** `analyze()` and `_build_bar_summary()` become fully testable, closing the 19% miss rate on `data_analyst.py`.

---

## ADR-006 — Create .claude/rules/01-security.md and .claude/imports/doctrine-summary.md (codex/issue-70)

**Date:** 2026-05-27
**Issue:** #70
**Context:** CLAUDE.md references `.claude/imports/doctrine-summary.md` and `.claude/rules/01-security.md` which do not exist, causing silent failures at Step 5 of the mandatory turn-start ritual.
**Decision:** Create both files with the relevant content: (a) doctrine-summary.md as a condensed operational checklist, (b) 01-security.md with STRIDE rules specific to this AI trading system.
**Alternative rejected:** Remove the `@import` reference from CLAUDE.md — the files should exist per the stated doctrine.

## ADR-007 — Audit-only pass records evidence without code remediation

**Date:** 2026-05-27
**Context:** User requested audit-only FDD+FSV pass and explicit prohibition on implementing fixes. Multiple quality/analyzer failures were detected.
**Decision:** Record full forensic evidence in memory files and hand off remediation to downstream implementation agent; do not modify production/test logic in this pass.
**Consequences:** Repository remains functionally test-green but non-compliant on ruff/mypy/tooling gates until implementation cycle.

## ADR-008 — Restamp RiskDecision hash after deterministic execution conditions (codex/issue-108)

**Date:** 2026-05-28
**Issue:** #108
**Context:** `ExecutionGate.validate()` correctly binds a `RiskDecision` to a `TradeProposal` by hash before execution. `ExecutionAgent._apply_conditions()` may deterministically reduce position size under Risk Manager conditions, which changes the proposal hash after the first gate check.
**Decision:** Treat deterministic Risk Manager execution conditions as part of the approved decision envelope: after conditions create an effective proposal with a new hash, update `risk_decision.proposal_hash` to the effective proposal hash and immediately call `ExecutionGate.validate()` again before any trade or fill is created.
**Alternatives rejected:** Leaving a documented hash mismatch preserves a known audit gap; forcing a full new risk cycle for deterministic risk-reducing size cuts is heavier than the current architecture requires.
**Edge cases covered:** no-op unknown condition, 50% reduction, 99% max reduction/minimum one share, duplicate reduction conditions.
