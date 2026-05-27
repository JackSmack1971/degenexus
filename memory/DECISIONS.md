# DECISIONS

Architecture decisions and audit findings requiring downstream implementation choices. Ordered newest-first.

---

## ADR-005 — CLAUDE.md Doctrine File Resolution (2026-05-27)

**Context:** `.claude/imports/doctrine-summary.md` and `.claude/rules/01-security.md` do not exist. Issue #70 tracks this.

**Decision options:**
1. Create `.claude/imports/doctrine-summary.md` — condensed operational checklist
2. Create `.claude/rules/01-security.md` — STRIDE/OWASP security rules for this AI trading system
3. Remove dead `@import` and `*See .claude/rules/*` references from CLAUDE.md (minimal option)

**Recommended:** Option 2 + 1 together. The missing security rules are the higher priority — this project uses LLM APIs, processes market data from external sources, and has prompt injection guards that need a documented policy basis.

**Tracking:** Issue #70
**Status:** PENDING IMPLEMENTATION

---

## ADR-004 — DataAnalystAgent DI Pattern (2026-05-27)

**Context:** `DataAnalystAgent.__init__` hard-instantiates `MarketFeed` and `IndicatorEngine`. Issue #69 tracks this.

**Decision:** Apply the same DI pattern used to fix issue #57 (PortfolioManagerAgent.feed):
```python
def __init__(
    self,
    performance_context: str = "",
    *,
    feed: Optional[MarketFeed] = None,
    engine: Optional[IndicatorEngine] = None,
) -> None:
    self.feed = feed or MarketFeed(alpha_vantage_key=None)
    self.engine = engine or IndicatorEngine()
```

**Rationale:** Consistent with the existing DI pattern; backward-compatible (default behaviour unchanged); enables test isolation without `__new__` workarounds.

**Edge cases to test:** feed returns < 30 bars; feed raises; engine.compute_all raises; all indicators None.

**Tracking:** Issue #69
**Status:** PENDING IMPLEMENTATION

---

## ADR-003 — orchestrator.py close_reason None guard (2026-05-27)

**Context:** `ct.close_reason.value` on `Optional[CloseReason]` at orchestrator.py:99. Issue #67 tracks this.

**Decision:** Use `ct.close_reason.value if ct.close_reason else "UNKNOWN"` inline. Do NOT change the model field to `CloseReason` (non-optional) — trades can legitimately exist without a close reason (e.g., partially closed state).

**Rationale:** Minimal, targeted fix. The model type `Optional[CloseReason]` is correct — the consumption site was wrong.

**Tracking:** Issue #67
**Status:** PENDING IMPLEMENTATION

---

## ADR-002 — ta dependency resolution (2026-05-27)

**Context:** `ta>=0.11.0` fails to build on Python 3.11 Linux. 11 tests fail. Issue #66 tracks this.

**Decision options (for downstream agent to evaluate):**
1. Replace `ta` with `pandas-ta` (pure Python, no C extensions) — requires updating `IndicatorEngine` imports
2. Pin `ta` to a version with pre-built wheels for Python 3.11 — check PyPI for available wheels
3. Change test mock strategy: inject `sys.modules["ta"]` as `MagicMock()` rather than patching `ta.volatility.BollingerBands` by string path

**Recommended:** Option 3 (test fix) + Option 2 (dependency pin) together. Option 1 is a larger refactor.

**Tracking:** Issue #66
**Status:** PENDING IMPLEMENTATION

---

## ADR-001 — mypy type narrowing pattern (2026-05-27)

**Context:** Two mypy violations: execution_agent.py:48 and data_analyst.py:119. Issue #68 tracks this.

**Decision:**
- `execution_agent.py:48`: Add `assert risk_decision is not None` after `gate.validate()` — this documents the invariant and satisfies mypy without changing runtime behaviour
- `data_analyst.py:119`: Change `direction=str(...).upper()` to `direction=Direction(str(...).upper())` — explicit enum construction is cleaner than relying on implicit Pydantic coercion

**Rationale:** `assert` over `if` for post-condition invariants (gate guarantees non-None after raising). Explicit `Direction(...)` construction over implicit Pydantic coercion.

**Tracking:** Issue #68
**Status:** PENDING IMPLEMENTATION

---

## Historical Decisions (carried forward from Cycle 1/2)

### DI Remediation Scope (Cycle 2 — issues #51/#57)
- `TradingOrchestrator`: `portfolio`, `trade_store`, `risk_gate` are now injectable
- `PortfolioManagerAgent`: `feed` is now injectable (fixed in #57)
- **Remaining gap**: `PerformanceAnalytics` and `ContextInjector` still hard-instantiated in TradingOrchestrator — NOT flagged as a priority since they have no external I/O in their constructors

### FSV Source-of-Truth Assignments
- Capital / positions: `Portfolio` in-memory
- Trade history SoT: `TradeStore` (SQLite WAL, `memory/trading_history.db`)
- Trade state machine SoT: `TradeLifecycle` (VALID_TRANSITIONS enforced)
- Test coverage SoT: `pytest --cov=src --cov-report=term-missing`
- Type safety SoT: `python -m mypy src/ --ignore-missing-imports`
- Complexity SoT: `python -m radon cc src/ -a -s`
