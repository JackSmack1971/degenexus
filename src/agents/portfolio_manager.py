"""Portfolio Manager Agent: monitors open positions, triggers TP/SL closures."""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional, Callable

from .base_agent import BaseAgent
from ..core.portfolio import Portfolio
from ..core.trade_lifecycle import TradeLifecycle
from ..models.trade import Trade, Position, TradeState, CloseReason, Direction
from ..data.market_feed import MarketFeed

logger = logging.getLogger(__name__)


class PortfolioManagerAgent(BaseAgent):

    def __init__(
        self,
        portfolio: Portfolio,
        performance_context: str = "",
        event_callback: Optional[Callable] = None,
    ) -> None:
        super().__init__("PORTFOLIO_MANAGER", performance_context)
        self.portfolio = portfolio
        self.lifecycle = TradeLifecycle()
        self.feed = MarketFeed()
        self._event_callback = event_callback or (lambda etype, content: None)
        self._open_trades: dict[str, Trade] = {}
        self._trade_to_position: dict[str, str] = {}
        self._partial_tp_flags: set[str] = set()

    def _emit(self, event_type: str, content: str) -> None:
        self._event_callback(event_type, content)

    def register_trade(self, trade: Trade, position: Position) -> None:
        """Called by Orchestrator after execution to register open trade."""
        self._open_trades[trade.trade_id] = trade
        self.portfolio.open_position(position)
        self._trade_to_position[trade.trade_id] = position.position_id
        logger.info(
            "PM: registered %s %s %d @ $%.4f",
            trade.direction.value, trade.symbol, trade.shares, trade.fill_price
        )

    def monitor_cycle(self) -> list[Trade]:
        """
        Checks all open positions against current prices.
        Closes any that hit TP or SL.
        Returns list of trades closed this cycle.
        """
        closed_trades: list[Trade] = []

        for trade_id, trade in list(self._open_trades.items()):
            if trade.state not in {TradeState.OPEN, TradeState.PARTIALLY_CLOSED}:
                continue

            current_price = self.feed.get_current_price(trade.symbol)
            if current_price is None:
                logger.warning("PM: cannot get price for %s, holding", trade.symbol)
                continue

            # Update mark-to-market for corresponding position
            pos_id = self._trade_to_position.get(trade_id)
            if pos_id:
                self.portfolio.update_position_price(pos_id, current_price)

            # Check partial TP
            if trade_id not in self._partial_tp_flags:
                if self.lifecycle.check_partial_tp(trade, current_price):
                    self._execute_partial_tp(trade, current_price, pos_id)
                    self._partial_tp_flags.add(trade_id)

            # Check full TP/SL
            close_reason = self.lifecycle.check_tp_sl(trade, current_price)
            if close_reason:
                closed_trade = self._close_trade(trade, current_price, close_reason, pos_id)
                closed_trades.append(closed_trade)
                del self._open_trades[trade_id]
                self._trade_to_position.pop(trade_id, None)
                self._partial_tp_flags.discard(trade_id)

        # Emit a single mark-to-market snapshot if any positions remain open
        remaining = [t for t in self._open_trades.values()
                     if t.state in {TradeState.OPEN, TradeState.PARTIALLY_CLOSED}]
        if remaining:
            lines = []
            for t in remaining:
                pos_id = self._trade_to_position.get(t.trade_id)
                pos = self.portfolio.open_positions.get(pos_id) if pos_id else None
                pnl_str = f"${pos.unrealized_pnl:+.2f}" if pos else "N/A"
                lines.append(f"{t.symbol} {t.direction.value} {t.shares}sh | UnrPnL: {pnl_str}")
            self._emit("POSITIONS_MTM", " | ".join(lines))

        return closed_trades

    def _close_trade(
        self,
        trade: Trade,
        close_price: float,
        reason: CloseReason,
        position_id: Optional[str],
    ) -> Trade:
        if trade.state == TradeState.PARTIALLY_CLOSED:
            partial_pnl = self._get_partial_pnl(trade)
        else:
            partial_pnl = 0.0

        closed = self.lifecycle.close_trade(trade, close_price, reason, partial_pnl)

        if position_id:
            self.portfolio.close_position(position_id, close_price, closed)

        logger.info(
            "PM: CLOSED %s %s @ $%.4f | reason: %s | PnL: $%+.2f",
            closed.symbol, closed.direction.value, close_price,
            reason.value, closed.realized_pnl,
        )

        if closed.realized_pnl is not None and closed.realized_pnl < 0:
            streak = self.portfolio.consecutive_losses
            self._emit(
                "CONSECUTIVE_LOSS",
                f"{closed.symbol} closed at a loss (${closed.realized_pnl:+.2f}) | "
                f"consecutive losses: {streak}",
            )

        return closed

    def _execute_partial_tp(
        self,
        trade: Trade,
        current_price: float,
        position_id: Optional[str],
    ) -> None:
        shares_to_close = max(1, trade.shares // 2)

        # Guard: skip if partial close would be a full close — let TP/SL handle it
        if shares_to_close >= trade.shares:
            logger.info(
                "PM: PARTIAL_TP skipped for %s — shares_to_close=%d >= trade.shares=%d; delegating to TP/SL",
                trade.symbol, shares_to_close, trade.shares,
            )
            return

        pnl = 0.0
        if position_id:
            pnl = self.portfolio.partial_close_position(position_id, current_price, shares_to_close)
            logger.info(
                "PM: PARTIAL_TP %s — closed %d/%d shares @ $%.4f | PnL: $%+.2f",
                trade.symbol, shares_to_close, trade.shares, current_price, pnl,
            )
        self.lifecycle.transition(trade, TradeState.PARTIALLY_CLOSED)
        trade.partial_pnl += pnl
        trade.shares -= shares_to_close
        self._emit(
            "PARTIAL_TP",
            f"{trade.symbol}: closed {shares_to_close}/{trade.shares + shares_to_close} shares "
            f"@ ${current_price:.2f} | PnL: ${pnl:+.2f} | remaining: {trade.shares}sh",
        )

    def _get_partial_pnl(self, trade: Trade) -> float:
        return trade.partial_pnl

    def open_trades_summary(self) -> str:
        if not self._open_trades:
            return "No open positions."
        lines = []
        for t in self._open_trades.values():
            pos_id = self._trade_to_position.get(t.trade_id)
            pos = self.portfolio.open_positions.get(pos_id) if pos_id else None
            pnl_str = f"${pos.unrealized_pnl:+.2f}" if pos else "N/A"
            lines.append(
                f"  {t.symbol} {t.direction.value} {t.shares}sh "
                f"@ ${t.fill_price:.2f} | SL:${t.stop_loss:.2f} TP:${t.take_profit:.2f} "
                f"| UnrPnL: {pnl_str}"
            )
        return "\n".join(lines)

    def _fallback(self, context: str) -> dict:
        return {}
