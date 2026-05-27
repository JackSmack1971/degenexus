# DECISIONS

## ADR-001 — Pin setuptools<65 for ta wheel compatibility (codex/issue-66)

**Date:** 2026-05-27  
**Issue:** #66  
**Context:** `ta>=0.11.0` uses legacy distutils commands incompatible with setuptools>=65. CI containers and Python 3.11 environments cannot build the `ta` wheel without this pin.  
**Decision:** Add `setuptools<65` to `requirements.txt` before `ta>=0.11.0`. This is the minimal fix that restores `ta` installation capability without replacing the library.  
**Alternatives rejected:**
- Replace `ta` with `pandas-ta` — not available for Python <3.12 in this environment
- Remove `ta` entirely — would require rewriting `IndicatorEngine` 
- Ignore (suppress) the build error — unacceptable; CI must be green  
**Trade-offs:** setuptools<65 is a narrow constraint. Monitor for conflicts with future packages that require newer setuptools.  
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
