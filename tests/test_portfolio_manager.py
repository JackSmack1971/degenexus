"""Tests for PortfolioManagerAgent partial take-profit accounting and position tracking."""

import uuid
from unittest.mock import MagicMock

from src.agents.portfolio_manager import PortfolioManagerAgent
from src.core.portfolio import Portfolio
from src.data.market_feed import MarketFeed
from src.models.trade import (
    CloseReason,
    Direction,
    OrderType,
    Position,
    Trade,
    TradeState,
)


def make_open_trade(symbol: str, shares: int, fill_price: float) -> Trade:
    return Trade(
        proposal_id=str(uuid.uuid4()),
        signal_id=str(uuid.uuid4()),
        symbol=symbol,
        direction=Direction.LONG,
        state=TradeState.OPEN,
        order_type=OrderType.LIMIT,
        entry_price=fill_price,
        fill_price=fill_price,
        shares=shares,
        gross_value=fill_price * shares,
        stop_loss=fill_price - 30.0,
        take_profit=fill_price + 30.0,
        max_loss_usd=shares * 2.0,
        risk_reward_ratio=2.5,
    )


def make_position_for_trade(trade: Trade) -> Position:
    return Position(
        trade_id=trade.trade_id,
        symbol=trade.symbol,
        direction=trade.direction,
        shares=trade.shares,
        entry_price=trade.fill_price,
        current_price=trade.fill_price,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
    )


def test_partial_tp_is_included_in_final_realized_pnl():
    portfolio = Portfolio(starting_capital=10_000.0)
    agent = PortfolioManagerAgent(portfolio=portfolio)

    trade = make_open_trade(symbol="AAPL", shares=10, fill_price=150.0)
    trade.stop_loss = 147.5
    trade.take_profit = 155.0
    trade.max_loss_usd = 25.0
    position = make_position_for_trade(trade)

    agent.register_trade(trade, position)

    agent._execute_partial_tp(trade, current_price=151.0, position_id=position.position_id)
    closed = agent._close_trade(
        trade,
        close_price=152.0,
        reason=CloseReason.TAKE_PROFIT,
        position_id=position.position_id,
    )

    assert closed.partial_pnl == 5.0
    assert closed.realized_pnl == 15.0


def test_monitor_cycle_updates_each_duplicate_symbol_position():
    portfolio = Portfolio(starting_capital=10_000.0)
    agent = PortfolioManagerAgent(portfolio=portfolio)

    trade_a = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
    trade_b = make_open_trade(symbol="AAPL", shares=5, fill_price=120.0)
    position_a = make_position_for_trade(trade_a)
    position_b = make_position_for_trade(trade_b)

    agent.register_trade(trade_a, position_a)
    agent.register_trade(trade_b, position_b)
    agent.feed.get_current_price = lambda symbol: 123.0

    agent.monitor_cycle()

    positions = portfolio.open_positions
    assert positions[position_a.position_id].current_price == 123.0
    assert positions[position_b.position_id].current_price == 123.0


# ---------------------------------------------------------------------------
# Additional tests for lines 36, 65, 69-70, 80-81, 86-90, 116, 130-131,
# 149-153, 166, 177-189, 192
# ---------------------------------------------------------------------------

class TestInitWithTradeStore:
    """Line 36 -- _partial_tp_flags seeded from DB when trade_store is provided."""

    def test_partial_tp_flags_seeded_from_db(self):
        ts = MagicMock()
        ts.get_partially_closed_trade_ids.return_value = ["abc", "def"]
        agent = PortfolioManagerAgent(
            portfolio=Portfolio(starting_capital=1_000.0),
            trade_store=ts,
        )
        assert "abc" in agent._partial_tp_flags
        assert "def" in agent._partial_tp_flags

    def test_partial_tp_flags_empty_when_no_trade_store(self):
        agent = PortfolioManagerAgent(portfolio=Portfolio(starting_capital=1_000.0))
        assert agent._partial_tp_flags == set()


class TestMonitorCycleTerminalStateTrade:
    """Line 65 -- trade in non-OPEN/PARTIALLY_CLOSED state is skipped."""

    def test_terminal_state_trade_not_closed_again(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)
        trade.state = TradeState.CANCELLED

        closed = agent.monitor_cycle()

        assert closed == []
        assert trade.trade_id in agent._open_trades


class TestMonitorCyclePriceNone:
    """Lines 69-70 -- feed returns None; trade is preserved."""

    def test_price_none_trade_stays_open(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)
        agent.feed.get_current_price = lambda s: None

        closed = agent.monitor_cycle()

        assert closed == []
        assert trade.state == TradeState.OPEN
        assert trade.trade_id in agent._open_trades


class TestMonitorCyclePartialTP:
    """Lines 80-81 -- partial TP triggered via monitor_cycle."""

    def test_partial_tp_dispatched_when_price_hits_level(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        events: list[tuple[str, str]] = []
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="TSLA", shares=10, fill_price=100.0)
        trade.stop_loss = 90.0
        trade.take_profit = 200.0
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent.feed.get_current_price = lambda s: 115.0

        closed = agent.monitor_cycle()

        assert closed == []
        assert trade.state == TradeState.PARTIALLY_CLOSED
        assert trade.trade_id in agent._partial_tp_flags
        assert any(etype == "PARTIAL_TP" for etype, _ in events)

    def test_partial_tp_not_re_triggered_when_already_flagged(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        events: list[tuple[str, str]] = []
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="TSLA", shares=10, fill_price=100.0)
        trade.stop_loss = 90.0
        trade.take_profit = 200.0
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)
        agent._partial_tp_flags.add(trade.trade_id)
        agent.feed.get_current_price = lambda s: 115.0

        agent.monitor_cycle()

        partial_tp_events = [e for e in events if e[0] == "PARTIAL_TP"]
        assert partial_tp_events == []


class TestMonitorCycleFullClose:
    """Lines 86-90 -- full TP/SL close path."""

    def test_take_profit_triggers_full_close(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        tp_price = trade.take_profit
        agent.feed.get_current_price = lambda s: tp_price

        closed = agent.monitor_cycle()

        assert len(closed) == 1
        closed_trade = closed[0]
        assert closed_trade.state == TradeState.CLOSED
        assert closed_trade.close_reason == CloseReason.TAKE_PROFIT
        assert trade.trade_id not in agent._open_trades

    def test_stop_loss_triggers_full_close(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        sl_price = trade.stop_loss
        agent.feed.get_current_price = lambda s: sl_price

        closed = agent.monitor_cycle()

        assert len(closed) == 1
        assert closed[0].close_reason == CloseReason.STOP_LOSS
        assert trade.trade_id not in agent._open_trades

    def test_partial_tp_flags_cleared_on_full_close(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)
        agent._partial_tp_flags.add(trade.trade_id)

        agent.feed.get_current_price = lambda s: trade.take_profit

        agent.monitor_cycle()

        assert trade.trade_id not in agent._partial_tp_flags


class TestCloseTradeOpenBranch:
    """Line 116 -- _close_trade for OPEN (non-partial) trade sets partial_pnl=0."""

    def test_close_open_trade_partial_pnl_zero(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        assert trade.state == TradeState.OPEN

        closed = agent._close_trade(
            trade,
            close_price=110.0,
            reason=CloseReason.TAKE_PROFIT,
            position_id=position.position_id,
        )

        assert closed.realized_pnl == (110.0 - 100.0) * 10
        assert closed.close_reason == CloseReason.TAKE_PROFIT


class TestCloseTradeConsecutiveLoss:
    """Lines 130-131 -- negative PnL emits CONSECUTIVE_LOSS event."""

    def test_loss_emits_consecutive_loss_event(self):
        events: list[tuple[str, str]] = []
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._close_trade(
            trade,
            close_price=90.0,
            reason=CloseReason.STOP_LOSS,
            position_id=position.position_id,
        )

        loss_events = [e for e in events if e[0] == "CONSECUTIVE_LOSS"]
        assert len(loss_events) == 1
        assert "AAPL" in loss_events[0][1]

    def test_win_does_not_emit_consecutive_loss_event(self):
        events: list[tuple[str, str]] = []
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._close_trade(
            trade,
            close_price=110.0,
            reason=CloseReason.TAKE_PROFIT,
            position_id=position.position_id,
        )

        assert not any(e[0] == "CONSECUTIVE_LOSS" for e in events)

    def test_breakeven_does_not_emit_consecutive_loss_event(self):
        """BVA: realized_pnl == 0 is not a loss."""
        events: list[tuple[str, str]] = []
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._close_trade(
            trade,
            close_price=100.0,
            reason=CloseReason.MANUAL,
            position_id=position.position_id,
        )

        assert not any(e[0] == "CONSECUTIVE_LOSS" for e in events)


class TestExecutePartialTPOneShareGuard:
    """Lines 149-153 -- 1-share trade skips partial TP execution."""

    def test_one_share_guard_returns_early(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        ts = MagicMock()
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            trade_store=ts,
        )

        trade = make_open_trade(symbol="AAPL", shares=1, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._execute_partial_tp(trade, current_price=115.0, position_id=position.position_id)

        assert trade.state == TradeState.OPEN
        ts.upsert_trade.assert_not_called()

    def test_two_share_trade_executes_partial_tp(self):
        """BVA: 2-share boundary -- shares_to_close=1 < 2, so partial TP proceeds."""
        portfolio = Portfolio(starting_capital=10_000.0)
        ts = MagicMock()
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            trade_store=ts,
        )

        trade = make_open_trade(symbol="AAPL", shares=2, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._execute_partial_tp(trade, current_price=115.0, position_id=position.position_id)

        assert trade.state == TradeState.PARTIALLY_CLOSED
        ts.upsert_trade.assert_called_once_with(trade)


class TestExecutePartialTPStoreUpsert:
    """Line 166 -- upsert_trade called when trade_store is provided."""

    def test_upsert_trade_called_after_partial_tp(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        ts = MagicMock()
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            trade_store=ts,
        )

        trade = make_open_trade(symbol="TSLA", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._execute_partial_tp(trade, current_price=115.0, position_id=position.position_id)

        ts.upsert_trade.assert_called_once_with(trade)

    def test_upsert_trade_not_called_without_trade_store(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="TSLA", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent._execute_partial_tp(trade, current_price=115.0, position_id=position.position_id)
        assert trade.state == TradeState.PARTIALLY_CLOSED


class TestOpenTradesSummary:
    """Lines 177-189 -- open_trades_summary formats active positions."""

    def test_summary_no_open_trades(self):
        agent = PortfolioManagerAgent(portfolio=Portfolio(starting_capital=1_000.0))
        assert agent.open_trades_summary() == "No open positions."

    def test_summary_one_open_trade(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=150.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        summary = agent.open_trades_summary()

        assert "AAPL" in summary
        assert "LONG" in summary
        assert "10sh" in summary
        assert "150.00" in summary

    def test_summary_contains_unrealized_pnl(self):
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        trade = make_open_trade(symbol="TSLA", shares=5, fill_price=200.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)
        portfolio.update_position_price(position.position_id, 210.0)

        summary = agent.open_trades_summary()

        assert "UnrPnL" in summary
        assert "$" in summary

    def test_summary_multiple_trades(self):
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio)

        for symbol in ["AAPL", "TSLA", "MSFT"]:
            t = make_open_trade(symbol=symbol, shares=5, fill_price=100.0)
            p = make_position_for_trade(t)
            agent.register_trade(t, p)

        summary = agent.open_trades_summary()
        assert "AAPL" in summary
        assert "TSLA" in summary
        assert "MSFT" in summary


class TestFallback:
    """Line 192 -- _fallback returns empty dict."""

    def test_fallback_returns_empty_dict(self):
        agent = PortfolioManagerAgent(portfolio=Portfolio(starting_capital=1_000.0))
        result = agent._fallback("any context")
        assert result == {}


# ---------------------------------------------------------------------------
# Issue #57 -- MarketFeed dependency injection tests
# ---------------------------------------------------------------------------

class FakeMarketFeed:
    """Deterministic feed that returns pre-configured prices per symbol."""

    def __init__(self, prices: dict[str, float | None]):
        self._prices = prices

    def get_current_price(self, symbol: str) -> float | None:
        return self._prices.get(symbol)


class TestMarketFeedDI:
    """Verify feed DI parameter: correct type, default fallback, and monitor_cycle integration."""

    def test_injected_feed_is_used(self):
        fake_feed = FakeMarketFeed({"AAPL": 150.0})
        agent = PortfolioManagerAgent(
            portfolio=Portfolio(starting_capital=10_000.0),
            feed=fake_feed,
        )
        assert agent.feed is fake_feed

    def test_default_feed_is_real_market_feed(self):
        agent = PortfolioManagerAgent(portfolio=Portfolio(starting_capital=10_000.0))
        assert isinstance(agent.feed, MarketFeed)

    def test_monitor_cycle_price_none_via_injected_feed(self):
        """Injected feed returning None -> trade preserved (lines 69-70)."""
        fake_feed = FakeMarketFeed({"AAPL": None})
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio, feed=fake_feed)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        closed = agent.monitor_cycle()

        assert closed == []
        assert trade.state == TradeState.OPEN

    def test_monitor_cycle_partial_tp_via_injected_feed(self):
        """Injected feed at partial-TP level triggers _execute_partial_tp (lines 80-81)."""
        fake_feed = FakeMarketFeed({"TSLA": 115.0})
        portfolio = Portfolio(starting_capital=50_000.0)
        events: list[tuple[str, str]] = []
        agent = PortfolioManagerAgent(
            portfolio=portfolio,
            feed=fake_feed,
            event_callback=lambda etype, content: events.append((etype, content)),
        )

        trade = make_open_trade(symbol="TSLA", shares=10, fill_price=100.0)
        trade.stop_loss = 90.0
        trade.take_profit = 200.0
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        agent.monitor_cycle()

        assert trade.state == TradeState.PARTIALLY_CLOSED
        assert any(e[0] == "PARTIAL_TP" for e in events)

    def test_monitor_cycle_full_close_via_injected_feed(self):
        """Injected feed at TP price triggers full close."""
        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        fake_feed = FakeMarketFeed({"AAPL": trade.take_profit})
        portfolio = Portfolio(starting_capital=50_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio, feed=fake_feed)

        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        closed = agent.monitor_cycle()

        assert len(closed) == 1
        assert closed[0].close_reason == CloseReason.TAKE_PROFIT

    def test_edge_case_feed_returns_nan(self):
        """feed.get_current_price returns float('nan') -- treated as valid price (not None guard)."""
        import math
        fake_feed = FakeMarketFeed({"AAPL": float("nan")})
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio, feed=fake_feed)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        closed = agent.monitor_cycle()
        assert isinstance(closed, list)
