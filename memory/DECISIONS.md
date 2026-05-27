# DECISIONS

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
