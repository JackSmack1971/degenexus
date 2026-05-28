"""Tests for PerformanceAnalytics.compute(), _compute_streak(), _compute_symbol_stats()."""

import pytest
from src.memory.performance import PerformanceAnalytics


def _trade(symbol: str, pnl: float, closed_at: str = "2026-01-01T00:00:00") -> dict:
    return {
        "symbol": symbol,
        "state": "CLOSED",
        "realized_pnl": pnl,
        "risk_reward_ratio": 2.0,
        "closed_at": closed_at,
    }


def _open_trade(symbol: str) -> dict:
    return {"symbol": symbol, "state": "OPEN", "realized_pnl": None}


@pytest.fixture
def analytics():
    return PerformanceAnalytics()


class TestComputeEmpty:

    def test_empty_list_returns_defaults(self, analytics):
        stats = analytics.compute([])
        assert stats.total_trades == 0
        assert stats.win_rate == 0.0
        assert stats.profit_factor == 0.0
        assert stats.current_streak == 0

    def test_no_closed_trades_returns_total_trades_only(self, analytics):
        stats = analytics.compute([_open_trade("AAPL"), _open_trade("GOOG")])
        assert stats.total_trades == 2
        assert stats.closed_trades == 0
        assert stats.win_rate == 0.0


class TestComputeWinsAndLosses:

    def test_all_wins_win_rate_1(self, analytics):
        trades = [_trade("A", 100), _trade("B", 200), _trade("C", 50)]
        stats = analytics.compute(trades)
        assert stats.win_rate == 1.0
        assert stats.win_count == 3
        assert stats.loss_count == 0
        assert stats.profit_factor == float("inf")

    def test_all_losses_win_rate_0(self, analytics):
        trades = [_trade("A", -100), _trade("B", -50)]
        stats = analytics.compute(trades)
        assert stats.win_rate == 0.0
        assert stats.win_count == 0
        assert stats.loss_count == 2
        assert stats.profit_factor == 0.0

    def test_mixed_trades_correct_win_rate(self, analytics):
        trades = [_trade("A", 100), _trade("B", -50), _trade("C", 200), _trade("D", -25)]
        stats = analytics.compute(trades)
        assert stats.win_rate == pytest.approx(0.5)
        assert stats.win_count == 2
        assert stats.loss_count == 2

    def test_profit_factor_computed_correctly(self, analytics):
        trades = [_trade("A", 100), _trade("B", 100), _trade("C", -50)]
        stats = analytics.compute(trades)
        # gross_profit=200, gross_loss=50 → PF=4.0
        assert stats.profit_factor == pytest.approx(4.0)

    def test_avg_win_avg_loss_computed_correctly(self, analytics):
        trades = [_trade("A", 100), _trade("B", 200), _trade("C", -50), _trade("D", -100)]
        stats = analytics.compute(trades)
        assert stats.avg_win_usd == pytest.approx(150.0)
        assert stats.avg_loss_usd == pytest.approx(75.0)

    def test_total_pnl_sum(self, analytics):
        trades = [_trade("A", 100), _trade("B", -30), _trade("C", 50)]
        stats = analytics.compute(trades)
        assert stats.total_pnl == pytest.approx(120.0)

    def test_total_trades_includes_open(self, analytics):
        trades = [_trade("A", 100), _open_trade("B")]
        stats = analytics.compute(trades)
        assert stats.total_trades == 2
        assert stats.closed_trades == 1


class TestComputeStreak:

    def test_all_wins_positive_streak(self, analytics):
        trades = [
            _trade("A", 10, "2026-01-01"),
            _trade("B", 20, "2026-01-02"),
            _trade("C", 30, "2026-01-03"),
        ]
        stats = analytics.compute(trades)
        assert stats.current_streak == 3

    def test_all_losses_negative_streak(self, analytics):
        trades = [
            _trade("A", -10, "2026-01-01"),
            _trade("B", -20, "2026-01-02"),
        ]
        stats = analytics.compute(trades)
        assert stats.current_streak == -2

    def test_streak_breaks_on_alternating(self, analytics):
        trades = [
            _trade("A", 10, "2026-01-01"),
            _trade("B", -5, "2026-01-02"),
            _trade("C", 20, "2026-01-03"),
        ]
        # Most recent is win → streak=1
        stats = analytics.compute(trades)
        assert stats.current_streak == 1

    def test_wins_then_loss_at_end(self, analytics):
        trades = [
            _trade("A", 100, "2026-01-01"),
            _trade("B", 100, "2026-01-02"),
            _trade("C", 100, "2026-01-03"),
            _trade("D", -50, "2026-01-04"),
        ]
        # Most recent is loss → streak=-1
        stats = analytics.compute(trades)
        assert stats.current_streak == -1

    def test_empty_closed_streak_is_zero(self, analytics):
        assert analytics._compute_streak([]) == 0


class TestStreakString:
    """_compute_streak indirectly via compute; direct unit test of _compute_streak."""

    def test_direct_positive_streak(self):
        analytics = PerformanceAnalytics()
        result = analytics._compute_streak([
            {"realized_pnl": 10, "closed_at": "2026-01-01"},
            {"realized_pnl": 20, "closed_at": "2026-01-02"},
        ])
        assert result == 2

    def test_direct_negative_streak(self):
        analytics = PerformanceAnalytics()
        result = analytics._compute_streak([
            {"realized_pnl": -10, "closed_at": "2026-01-01"},
            {"realized_pnl": -5, "closed_at": "2026-01-02"},
            {"realized_pnl": -1, "closed_at": "2026-01-03"},
        ])
        assert result == -3


class TestSymbolStats:

    def test_single_symbol_aggregation(self, analytics):
        trades = [_trade("AAPL", 100), _trade("AAPL", -50), _trade("AAPL", 200)]
        stats = analytics.compute(trades)
        s = stats.symbol_stats["AAPL"]
        assert s["trades"] == 3
        assert s["wins"] == 2
        assert s["pnl"] == pytest.approx(250.0)

    def test_multi_symbol_best_worst(self, analytics):
        trades = [
            _trade("AAPL", 500),
            _trade("GOOG", -200),
        ]
        stats = analytics.compute(trades)
        assert stats.best_symbol == "AAPL"
        assert stats.worst_symbol == "GOOG"

    def test_same_symbol_best_worst_not_repeated(self, analytics):
        trades = [_trade("AAPL", 100)]
        stats = analytics.compute(trades)
        # Only one symbol → best==worst, should not be output separately (worst != best check in injector)
        assert stats.best_symbol == "AAPL"
        assert stats.worst_symbol == "AAPL"


class TestClassifyTrades:
    """Unit tests for _classify_trades — covers breakeven bug fix (pnl=0.0 excluded)."""

    def test_breakeven_trade_excluded_from_wins_and_losses(self):
        """pnl=0.0 must not be counted as a win or loss — previously broken (was counted as loss)."""
        analytics = PerformanceAnalytics()
        trades = [
            {"realized_pnl": 100.0, "state": "CLOSED"},
            {"realized_pnl": 0.0, "state": "CLOSED"},
            {"realized_pnl": -50.0, "state": "CLOSED"},
        ]
        wins, losses = analytics._classify_trades(trades)
        assert len(wins) == 1
        assert len(losses) == 1

    def test_all_breakeven_returns_empty_wins_and_losses(self):
        analytics = PerformanceAnalytics()
        trades = [{"realized_pnl": 0.0}, {"realized_pnl": 0.0}]
        wins, losses = analytics._classify_trades(trades)
        assert wins == []
        assert losses == []

    def test_none_pnl_treated_as_zero(self):
        analytics = PerformanceAnalytics()
        trades = [{"realized_pnl": None}]
        wins, losses = analytics._classify_trades(trades)
        assert wins == []
        assert losses == []

    def test_breakeven_does_not_inflate_loss_count_in_compute(self):
        """Regression: breakeven trade via compute() must not appear in loss_count."""
        analytics = PerformanceAnalytics()
        trades = [
            {"symbol": "A", "state": "CLOSED", "realized_pnl": 100.0,
             "risk_reward_ratio": 2.0, "closed_at": "2026-01-01"},
            {"symbol": "B", "state": "CLOSED", "realized_pnl": 0.0,
             "risk_reward_ratio": 0.0, "closed_at": "2026-01-02"},
        ]
        stats = analytics.compute(trades)
        assert stats.win_count == 1
        assert stats.loss_count == 0
        assert stats.closed_trades == 2


class TestComputeTotals:
    """Unit tests for _compute_totals helper."""

    def test_total_pnl_is_sum_of_all_closed(self):
        analytics = PerformanceAnalytics()
        trades = [
            {"realized_pnl": 100.0, "risk_reward_ratio": 2.0},
            {"realized_pnl": -40.0, "risk_reward_ratio": 1.0},
        ]
        total_pnl, avg_rr = analytics._compute_totals(trades)
        assert total_pnl == pytest.approx(60.0)

    def test_avg_rr_is_mean_of_ratios(self):
        analytics = PerformanceAnalytics()
        trades = [
            {"realized_pnl": 50.0, "risk_reward_ratio": 2.0},
            {"realized_pnl": 50.0, "risk_reward_ratio": 4.0},
        ]
        _, avg_rr = analytics._compute_totals(trades)
        assert avg_rr == pytest.approx(3.0)

    def test_missing_rr_treated_as_zero(self):
        analytics = PerformanceAnalytics()
        trades = [{"realized_pnl": 50.0}]
        _, avg_rr = analytics._compute_totals(trades)
        assert avg_rr == pytest.approx(0.0)

    def test_none_pnl_treated_as_zero_in_total(self):
        analytics = PerformanceAnalytics()
        trades = [{"realized_pnl": None, "risk_reward_ratio": 2.0}]
        total_pnl, _ = analytics._compute_totals(trades)
        assert total_pnl == pytest.approx(0.0)
