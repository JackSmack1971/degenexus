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
        lc = TradeLifecycle()
        t = make_proposed_trade()
        t.state = state
        assert t.is_terminal is True

    def test_open_is_not_terminal(self):
        lc = TradeLifecycle()
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
