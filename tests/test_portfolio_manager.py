"""Tests for PortfolioManagerAgent position tracking."""

import uuid

from src.agents.portfolio_manager import PortfolioManagerAgent
from src.core.portfolio import Portfolio
from src.models.trade import Direction, OrderType, Position, Trade, TradeState


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
