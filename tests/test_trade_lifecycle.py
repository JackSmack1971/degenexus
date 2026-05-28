"""Tests for TradeLifecycle state machine — no incomplete trades allowed."""

import pytest
import uuid
from src.core.trade_lifecycle import TradeLifecycle, TradeLifecycleError
from src.models.trade import Trade, TradeState, Direction, OrderType, CloseReason, TERMINAL_STATES


def make_proposed_trade():
    return Trade(
        proposal_id=str(uuid.uuid4()),
        signal_id=str(uuid.uuid4()),
        symbol="AAPL",
        direction=Direction.LONG,
        state=TradeState.PROPOSED,
        order_type=OrderType.LIMIT,
        entry_price=150.0,
        fill_price=0.0,
        shares=10,
        stop_loss=147.5,
        take_profit=155.0,
        max_loss_usd=25.0,
        risk_reward_ratio=2.0,
    )


class TestValidTransitions:
    def test_proposed_to_risk_reviewed(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        assert t.state == TradeState.RISK_REVIEWED

    def test_full_happy_path_proposed_to_closed(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        t = lc.transition(t, TradeState.CEO_APPROVED)
        t = lc.transition(t, TradeState.QUEUED)
        t = lc.open_trade(t, fill_price=150.08, slippage_pct=0.00053)
        assert t.state == TradeState.OPEN
        assert t.fill_price == 150.08

        t = lc.close_trade(t, close_price=155.0, close_reason=CloseReason.TAKE_PROFIT)
        assert t.state == TradeState.CLOSED
        assert t.realized_pnl == pytest.approx((155.0 - 150.08) * 10, abs=0.01)

    def test_proposed_can_be_dropped(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.DROPPED)
        assert t.state == TradeState.DROPPED

    def test_risk_reviewed_can_be_rejected(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        t = lc.transition(t, TradeState.REJECTED)
        assert t.state == TradeState.REJECTED


class TestInvalidTransitions:
    def test_cannot_skip_risk_review(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        with pytest.raises(TradeLifecycleError):
            lc.transition(t, TradeState.CEO_APPROVED)

    def test_cannot_go_from_open_to_proposed(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        t = lc.transition(t, TradeState.CEO_APPROVED)
        t = lc.transition(t, TradeState.QUEUED)
        t = lc.open_trade(t, 150.0, 0.0)
        with pytest.raises(TradeLifecycleError):
            lc.transition(t, TradeState.PROPOSED)

    def test_cannot_transition_from_terminal_state(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.DROPPED)
        with pytest.raises(TradeLifecycleError):
            lc.transition(t, TradeState.RISK_REVIEWED)


class TestTerminalStates:
    @pytest.mark.parametrize("state", list(TERMINAL_STATES))
    def test_all_terminal_states_are_final(self, state):
        t = make_proposed_trade()
        t.state = state
        assert t.is_terminal is True

    def test_open_is_not_terminal(self):
        t = make_proposed_trade()
        t.state = TradeState.OPEN
        assert t.is_terminal is False


class TestPnLCalculation:
    def test_long_trade_win_pnl(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        t = lc.transition(t, TradeState.CEO_APPROVED)
        t = lc.transition(t, TradeState.QUEUED)
        t = lc.open_trade(t, 150.0, 0.0)
        t = lc.close_trade(t, 155.0, CloseReason.TAKE_PROFIT)
        assert t.realized_pnl == pytest.approx(50.0, abs=0.01)

    def test_long_trade_loss_pnl(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t = lc.transition(t, TradeState.RISK_REVIEWED)
        t = lc.transition(t, TradeState.CEO_APPROVED)
        t = lc.transition(t, TradeState.QUEUED)
        t = lc.open_trade(t, 150.0, 0.0)
        t = lc.close_trade(t, 147.5, CloseReason.STOP_LOSS)
        assert t.realized_pnl == pytest.approx(-25.0, abs=0.01)

    def test_close_reason_recorded(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        for s in [TradeState.RISK_REVIEWED, TradeState.CEO_APPROVED, TradeState.QUEUED]:
            t = lc.transition(t, s)
        t = lc.open_trade(t, 150.0, 0.0)
        t = lc.close_trade(t, 147.5, CloseReason.STOP_LOSS)
        assert t.close_reason == CloseReason.STOP_LOSS


def make_open_short_trade(fill_price: float = 100.0, stop_loss: float = 105.0, take_profit: float = 90.0, shares: int = 10) -> Trade:
    t = Trade(
        proposal_id=str(uuid.uuid4()),
        signal_id=str(uuid.uuid4()),
        symbol="TSLA",
        direction=Direction.SHORT,
        state=TradeState.OPEN,
        order_type=OrderType.LIMIT,
        fill_price=fill_price,
        gross_value=fill_price * shares,
        shares=shares,
        stop_loss=stop_loss,
        take_profit=take_profit,
    )
    return t


class TestShortPnL:
    def test_short_trade_profit(self):
        """SHORT: price falls → profit = (fill - close) * shares"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=110.0, stop_loss=115.0, take_profit=100.0, shares=10)
        t = lc.close_trade(t, close_price=100.0, close_reason=CloseReason.TAKE_PROFIT)
        assert t.realized_pnl == pytest.approx(100.0, abs=0.01)

    def test_short_trade_loss(self):
        """SHORT: price rises → loss = (fill - close) * shares (negative)"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=110.0, take_profit=90.0, shares=10)
        t = lc.close_trade(t, close_price=110.0, close_reason=CloseReason.STOP_LOSS)
        assert t.realized_pnl == pytest.approx(-100.0, abs=0.01)

    def test_short_zero_pnl_at_fill(self):
        """SHORT: close at fill price → zero PnL"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0, shares=5)
        t = lc.close_trade(t, close_price=100.0, close_reason=CloseReason.MANUAL)
        assert t.realized_pnl == pytest.approx(0.0, abs=0.01)


class TestShortTpSlChecks:
    def test_short_stop_loss_trigger(self):
        """SHORT SL: price rises to/above stop_loss → STOP_LOSS"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0)
        assert lc.check_tp_sl(t, current_price=105.0) == CloseReason.STOP_LOSS
        assert lc.check_tp_sl(t, current_price=106.0) == CloseReason.STOP_LOSS

    def test_short_take_profit_trigger(self):
        """SHORT TP: price falls to/below take_profit → TAKE_PROFIT"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0)
        assert lc.check_tp_sl(t, current_price=90.0) == CloseReason.TAKE_PROFIT
        assert lc.check_tp_sl(t, current_price=89.0) == CloseReason.TAKE_PROFIT

    def test_short_in_range_returns_none(self):
        """SHORT: price between SL and TP → no close"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0)
        assert lc.check_tp_sl(t, current_price=95.0) is None

    def test_short_at_fill_price_no_trigger(self):
        """SHORT: price exactly at fill → no trigger"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0)
        assert lc.check_tp_sl(t, current_price=100.0) is None

    def test_short_stop_loss_bva_one_tick_below(self):
        """SHORT: one tick below SL does NOT trigger (strict >=)"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=105.0, take_profit=90.0)
        assert lc.check_tp_sl(t, current_price=104.99) is None


class TestPartialTpZeroDistance:
    def test_zero_risk_distance_returns_false(self):
        """fill == stop → risk_distance==0 must not trigger partial TP"""
        lc = TradeLifecycle()
        t = make_open_short_trade(fill_price=100.0, stop_loss=100.0, take_profit=90.0)
        assert lc.check_partial_tp(t, current_price=100.01) is False

    def test_non_zero_distance_long_triggers(self):
        lc = TradeLifecycle()
        t = Trade(
            proposal_id=str(uuid.uuid4()), signal_id=str(uuid.uuid4()),
            symbol="AAPL", direction=Direction.LONG, state=TradeState.OPEN,
            order_type=OrderType.LIMIT, fill_price=100.0, shares=10,
            stop_loss=95.0, take_profit=115.0,
        )
        # partial_tp_level = 100 + 1.5*5 = 107.5
        assert lc.check_partial_tp(t, current_price=107.5) is True
        assert lc.check_partial_tp(t, current_price=107.49) is False


class TestTpSlChecks:
    def test_detects_stop_loss_hit_long(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t.state = TradeState.OPEN
        result = lc.check_tp_sl(t, current_price=147.5)
        assert result == CloseReason.STOP_LOSS

    def test_detects_take_profit_hit_long(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t.state = TradeState.OPEN
        result = lc.check_tp_sl(t, current_price=155.0)
        assert result == CloseReason.TAKE_PROFIT

    def test_no_close_for_price_in_range(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t.state = TradeState.OPEN
        result = lc.check_tp_sl(t, current_price=152.0)
        assert result is None

    def test_no_check_if_not_open(self):
        lc = TradeLifecycle()
        t = make_proposed_trade()
        result = lc.check_tp_sl(t, current_price=147.0)
        assert result is None
