"""Tests for Portfolio: capital tracking and P&L math."""

import pytest
import uuid
from src.core.portfolio import Portfolio
from src.models.trade import Trade, Position, Direction, TradeState, OrderType, CloseReason


def make_trade(symbol="AAPL", direction=Direction.LONG, fill_price=150.0, shares=10,
               stop_loss=147.5, take_profit=155.0):
    t = Trade(
        proposal_id=str(uuid.uuid4()),
        signal_id=str(uuid.uuid4()),
        symbol=symbol,
        direction=direction,
        state=TradeState.OPEN,
        order_type=OrderType.LIMIT,
        entry_price=fill_price,
        fill_price=fill_price,
        shares=shares,
        gross_value=fill_price * shares,
        stop_loss=stop_loss,
        take_profit=take_profit,
        max_loss_usd=abs(fill_price - stop_loss) * shares,
        risk_reward_ratio=2.0,
    )
    return t


def make_position(trade, current_price=None):
    return Position(
        trade_id=trade.trade_id,
        symbol=trade.symbol,
        direction=trade.direction,
        shares=trade.shares,
        entry_price=trade.fill_price,
        current_price=current_price or trade.fill_price,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
    )


class TestInitialState:
    def test_starting_capital_set_correctly(self):
        p = Portfolio(starting_capital=10_000.0)
        assert p.starting_capital == 10_000.0
        assert p.cash == 10_000.0
        assert p.total_value == 10_000.0

    def test_zero_pnl_at_start(self):
        p = Portfolio(starting_capital=10_000.0)
        assert p.total_pnl == 0.0
        assert p.unrealized_pnl == 0.0

    def test_zero_drawdown_at_start(self):
        p = Portfolio(starting_capital=10_000.0)
        assert p.drawdown_pct == 0.0


class TestOpenPosition:
    def test_cash_deducted_on_open(self, portfolio, open_position):
        portfolio.open_position(open_position)
        assert portfolio.cash == 10_000.0 - open_position.entry_price * open_position.shares

    def test_total_value_unchanged_on_open(self, portfolio, open_position):
        portfolio.open_position(open_position)
        assert abs(portfolio.total_value - 10_000.0) < 0.01

    def test_position_tracked(self, portfolio, open_position):
        portfolio.open_position(open_position)
        assert open_position.position_id in portfolio.open_positions

    def test_raises_insufficient_cash(self):
        p = Portfolio(starting_capital=100.0)
        pos = Position(
            trade_id=str(uuid.uuid4()),
            symbol="AAPL",
            direction=Direction.LONG,
            shares=100,
            entry_price=150.0,
            current_price=150.0,
            stop_loss=147.5,
            take_profit=155.0,
        )
        with pytest.raises(ValueError, match="Insufficient cash"):
            p.open_position(pos)


class TestUpdatePrice:
    def test_unrealized_pnl_increases_with_price(self, portfolio, open_position):
        portfolio.open_position(open_position)
        portfolio.update_position_price(open_position.position_id, 155.0)
        assert portfolio.unrealized_pnl > 0

    def test_unrealized_pnl_decreases_with_price(self, portfolio, open_position):
        portfolio.open_position(open_position)
        portfolio.update_position_price(open_position.position_id, 145.0)
        assert portfolio.unrealized_pnl < 0

    def test_total_value_reflects_price_change(self, portfolio, open_position):
        portfolio.open_position(open_position)
        portfolio.update_position_price(open_position.position_id, 160.0)
        expected = portfolio.cash + 160.0 * open_position.shares
        assert abs(portfolio.total_value - expected) < 0.01


class TestClosePosition:
    def test_cash_credited_on_close(self, portfolio, open_position, valid_proposal):
        portfolio.open_position(open_position)
        trade = make_trade(fill_price=150.0, shares=10)
        trade.fill_price = 150.0
        trade.shares = 10
        trade.realized_pnl = (155.0 - 150.0) * 10
        cash_before = portfolio.cash
        portfolio.close_position(open_position.position_id, 155.0, trade)
        assert portfolio.cash > cash_before

    def test_position_removed_after_close(self, portfolio, open_position, valid_proposal):
        portfolio.open_position(open_position)
        trade = make_trade()
        trade.realized_pnl = 0
        portfolio.close_position(open_position.position_id, 150.0, trade)
        assert open_position.position_id not in portfolio.open_positions

    def test_consecutive_losses_incremented_on_loss(self, portfolio, open_position):
        portfolio.open_position(open_position)
        trade = make_trade()
        trade.realized_pnl = -25.0
        portfolio.close_position(open_position.position_id, 147.5, trade)
        assert portfolio.consecutive_losses == 1

    def test_consecutive_losses_reset_on_win(self, portfolio, open_position):
        portfolio._consecutive_losses = 2
        portfolio.open_position(open_position)
        trade = make_trade()
        trade.realized_pnl = 50.0
        portfolio.close_position(open_position.position_id, 155.0, trade)
        assert portfolio.consecutive_losses == 0

    def test_raises_for_nonexistent_position(self, portfolio, valid_proposal):
        trade = make_trade()
        trade.realized_pnl = 0
        with pytest.raises(KeyError):
            portfolio.close_position("nonexistent-id", 150.0, trade)


class TestPnL:
    def test_realized_pnl_accumulates(self, portfolio):
        for i in range(3):
            pos = Position(
                trade_id=str(uuid.uuid4()), symbol="SPY",
                direction=Direction.LONG, shares=5,
                entry_price=500.0, current_price=500.0,
                stop_loss=490.0, take_profit=520.0,
            )
            portfolio.open_position(pos)
            trade = make_trade(symbol="SPY", fill_price=500.0, shares=5)
            trade.realized_pnl = 50.0
            portfolio.close_position(pos.position_id, 510.0, trade)

        assert portfolio.win_count == 3
        assert portfolio.total_value > portfolio.starting_capital
