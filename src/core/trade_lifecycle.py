"""Trade state machine. Every trade must reach a terminal state."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional

from ..models.trade import Trade, TradeState, TERMINAL_STATES, CloseReason, Direction


class TradeLifecycleError(Exception):
    pass


VALID_TRANSITIONS: dict[TradeState, set[TradeState]] = {
    TradeState.PROPOSED: {TradeState.RISK_REVIEWED, TradeState.DROPPED},
    TradeState.RISK_REVIEWED: {TradeState.CEO_APPROVED, TradeState.REJECTED},
    TradeState.CEO_APPROVED: {TradeState.QUEUED, TradeState.DROPPED},
    TradeState.QUEUED: {TradeState.FILLED, TradeState.CANCELLED},
    TradeState.FILLED: {TradeState.OPEN, TradeState.CANCELLED},
    TradeState.OPEN: {
        TradeState.PARTIALLY_CLOSED,
        TradeState.CLOSED,
        TradeState.CANCELLED,
    },
    TradeState.PARTIALLY_CLOSED: {TradeState.CLOSED, TradeState.CANCELLED},
    TradeState.CLOSED: set(),
    TradeState.REJECTED: set(),
    TradeState.DROPPED: set(),
    TradeState.CANCELLED: set(),
}


class TradeLifecycle:
    """Enforces valid state transitions. No trade can skip states or re-open."""

    def transition(self, trade: Trade, new_state: TradeState) -> Trade:
        if trade.state in TERMINAL_STATES:
            raise TradeLifecycleError(
                f"Trade {trade.trade_id} is already in terminal state {trade.state}"
            )

        allowed = VALID_TRANSITIONS.get(trade.state, set())
        if new_state not in allowed:
            raise TradeLifecycleError(
                f"Invalid transition {trade.state} → {new_state} "
                f"(allowed: {allowed})"
            )

        trade.state = new_state
        return trade

    def open_trade(self, trade: Trade, fill_price: float, slippage_pct: float) -> Trade:
        self.transition(trade, TradeState.FILLED)
        trade.fill_price = fill_price
        trade.slippage_pct = slippage_pct
        trade.gross_value = fill_price * trade.shares
        self.transition(trade, TradeState.OPEN)
        trade.opened_at = datetime.now(timezone.utc)
        return trade

    def close_trade(
        self,
        trade: Trade,
        close_price: float,
        close_reason: CloseReason,
        partial_pnl: float = 0.0,
    ) -> Trade:
        self.transition(trade, TradeState.CLOSED)
        trade.close_price = close_price
        trade.close_reason = close_reason
        trade.close_shares = trade.shares
        trade.closed_at = datetime.now(timezone.utc)

        if trade.direction == Direction.LONG:
            raw_pnl = (close_price - trade.fill_price) * trade.shares
        else:
            raw_pnl = (trade.fill_price - close_price) * trade.shares

        trade.realized_pnl = raw_pnl + partial_pnl
        if trade.gross_value > 0:
            trade.realized_pnl_pct = trade.realized_pnl / trade.gross_value

        return trade

    def check_tp_sl(
        self,
        trade: Trade,
        current_price: float,
    ) -> Optional[CloseReason]:
        """Returns close reason if price has hit TP or SL, else None."""
        if trade.state not in {TradeState.OPEN, TradeState.PARTIALLY_CLOSED}:
            return None

        if trade.direction == Direction.LONG:
            if current_price <= trade.stop_loss:
                return CloseReason.STOP_LOSS
            if current_price >= trade.take_profit:
                return CloseReason.TAKE_PROFIT
        else:
            if current_price >= trade.stop_loss:
                return CloseReason.STOP_LOSS
            if current_price <= trade.take_profit:
                return CloseReason.TAKE_PROFIT

        return None

    def check_partial_tp(
        self,
        trade: Trade,
        current_price: float,
    ) -> bool:
        """
        Returns True if partial TP should trigger (price reached 1.5× risk distance).
        Only fires once per trade.
        """
        if trade.state != TradeState.OPEN:
            return False
        if hasattr(trade, "_partial_tp_triggered") and trade._partial_tp_triggered:
            return False

        risk_distance = abs(trade.fill_price - trade.stop_loss)
        partial_tp_level = trade.fill_price + 1.5 * risk_distance

        if trade.direction == Direction.LONG and current_price >= partial_tp_level:
            return True
        if trade.direction == Direction.SHORT and current_price <= partial_tp_level:
            return True

        return False
