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
# Issue #57 — MarketFeed dependency injection tests
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
        """Injected feed returning None → trade preserved (lines 69-70)."""
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
        # fill=100, stop=90 → risk=10 → partial_tp_level=115
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
        """feed.get_current_price returns float('nan') — treated as a valid price (not None guard)."""
        import math
        fake_feed = FakeMarketFeed({"AAPL": float("nan")})
        portfolio = Portfolio(starting_capital=10_000.0)
        agent = PortfolioManagerAgent(portfolio=portfolio, feed=fake_feed)

        trade = make_open_trade(symbol="AAPL", shares=10, fill_price=100.0)
        position = make_position_for_trade(trade)
        agent.register_trade(trade, position)

        # NaN is not None so the guard doesn't catch it — monitor_cycle runs without crashing
        closed = agent.monitor_cycle()
        assert isinstance(closed, list)  # no crash
