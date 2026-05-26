"""Tests for ContextInjector.build_context() and _streak_string()."""

import pytest
from src.memory.context_injector import ContextInjector
from src.memory.performance import PerformanceStats


@pytest.fixture
def injector():
    return ContextInjector()


def _stats(**kwargs) -> PerformanceStats:
    defaults = dict(
        total_trades=10,
        closed_trades=8,
        win_count=5,
        loss_count=3,
        win_rate=0.625,
        avg_win_usd=120.0,
        avg_loss_usd=60.0,
        profit_factor=3.33,
        total_pnl=300.0,
        current_streak=2,
        best_symbol="AAPL",
        worst_symbol="GOOG",
        symbol_stats={
            "AAPL": {"trades": 5, "wins": 4, "pnl": 400.0},
            "GOOG": {"trades": 3, "wins": 1, "pnl": -100.0},
        },
    )
    defaults.update(kwargs)
    return PerformanceStats(**defaults)


class _MockSnapshot:
    total_value = 10_000.0
    cash = 6_000.0
    invested = 4_000.0
    drawdown_pct = 0.05
    open_positions_count = 2


class _MockLimits:
    max_loss_pct_per_trade = 0.02
    max_open_positions = 5
    max_total_exposure_pct = 0.80
    min_confidence = 0.55
    min_risk_reward = 1.5
    max_consecutive_losses = 3


class TestBuildContextEmpty:

    def test_zero_trades_returns_empty_context(self, injector):
        ctx = injector.build_context(PerformanceStats())
        assert "No trade history" in ctx
        assert "first session" in ctx

    def test_zero_trades_ignores_snapshot(self, injector):
        ctx = injector.build_context(PerformanceStats(), portfolio_snapshot=_MockSnapshot())
        assert "PORTFOLIO STATE" not in ctx


class TestBuildContextCore:

    def test_win_rate_appears_in_context(self, injector):
        ctx = injector.build_context(_stats(win_rate=0.625))
        assert "62.5%" in ctx

    def test_total_pnl_appears(self, injector):
        ctx = injector.build_context(_stats(total_pnl=300.0))
        assert "+300" in ctx

    def test_profit_factor_inf_rendered_as_symbol(self, injector):
        ctx = injector.build_context(_stats(profit_factor=float("inf")))
        assert "∞" in ctx

    def test_best_and_worst_symbol_appear(self, injector):
        ctx = injector.build_context(_stats())
        assert "AAPL" in ctx
        assert "GOOG" in ctx

    def test_same_best_worst_symbol_not_duplicated(self, injector):
        s = _stats(
            best_symbol="AAPL",
            worst_symbol="AAPL",
            symbol_stats={"AAPL": {"trades": 3, "wins": 2, "pnl": 100.0}},
        )
        ctx = injector.build_context(s)
        # Weakest symbol line should NOT appear when worst==best
        assert "Weakest symbol" not in ctx

    def test_context_ends_with_end_marker(self, injector):
        ctx = injector.build_context(_stats())
        assert ctx.strip().endswith("=== END CONTEXT ===")


class TestBuildContextPortfolioSnapshot:

    def test_portfolio_section_present_with_snapshot(self, injector):
        ctx = injector.build_context(_stats(), portfolio_snapshot=_MockSnapshot())
        assert "PORTFOLIO STATE" in ctx
        assert "10,000" in ctx

    def test_portfolio_section_absent_without_snapshot(self, injector):
        ctx = injector.build_context(_stats())
        assert "PORTFOLIO STATE" not in ctx


class TestBuildContextRiskCapacity:

    def test_risk_capacity_section_with_snapshot_and_limits(self, injector):
        ctx = injector.build_context(
            _stats(),
            portfolio_snapshot=_MockSnapshot(),
            risk_limits=_MockLimits(),
        )
        assert "RISK CAPACITY" in ctx
        assert "Max positions: 5" in ctx

    def test_risk_capacity_absent_without_limits(self, injector):
        ctx = injector.build_context(_stats(), portfolio_snapshot=_MockSnapshot())
        assert "RISK CAPACITY" not in ctx

    def test_risk_capacity_absent_without_snapshot(self, injector):
        ctx = injector.build_context(_stats(), risk_limits=_MockLimits())
        assert "RISK CAPACITY" not in ctx


class TestBuildContextCautionBanner:

    def test_caution_banner_when_streak_lte_minus2(self, injector):
        ctx = injector.build_context(_stats(current_streak=-2))
        assert "CAUTION" in ctx
        assert "consecutive losses" in ctx

    def test_caution_banner_when_streak_minus3(self, injector):
        ctx = injector.build_context(_stats(current_streak=-3))
        assert "CAUTION" in ctx

    def test_no_caution_banner_when_streak_minus1(self, injector):
        ctx = injector.build_context(_stats(current_streak=-1))
        assert "CAUTION" not in ctx

    def test_no_caution_banner_on_win_streak(self, injector):
        ctx = injector.build_context(_stats(current_streak=5))
        assert "CAUTION" not in ctx


class TestBuildContextWatchlist:

    def test_watchlist_section_with_known_symbols(self, injector):
        ctx = injector.build_context(
            _stats(),
            watchlist=["AAPL", "GOOG", "MSFT"],
        )
        assert "WATCHLIST PERFORMANCE" in ctx
        assert "AAPL" in ctx
        assert "no history yet" in ctx  # MSFT has no stats

    def test_watchlist_section_absent_without_watchlist(self, injector):
        ctx = injector.build_context(_stats())
        assert "WATCHLIST PERFORMANCE" not in ctx


class TestStreakString:

    def test_positive_streak(self, injector):
        assert injector._streak_string(3) == "+3 wins in a row"

    def test_negative_streak(self, injector):
        assert injector._streak_string(-2) == "2 losses in a row"

    def test_zero_streak_neutral(self, injector):
        assert injector._streak_string(0) == "neutral"

    def test_positive_one(self, injector):
        assert injector._streak_string(1) == "+1 wins in a row"

    def test_negative_one(self, injector):
        assert injector._streak_string(-1) == "1 losses in a row"
