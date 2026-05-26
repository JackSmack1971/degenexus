"""Portfolio state: cash, positions, P&L tracking. Source of Truth for capital."""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field
import os

from ..models.trade import Position, Trade


@dataclass
class PortfolioSnapshot:
    timestamp: datetime
    total_value: float
    cash: float
    invested: float
    realized_pnl: float
    unrealized_pnl: float
    drawdown_pct: float
    open_positions_count: int
    win_count: int
    loss_count: int


class Portfolio:
    """
    Tracks capital, positions, and P&L.
    This is the SoT for all financial state — agents read from here,
    never from their own cached memory.
    """

    def __init__(self, starting_capital: float | None = None) -> None:
        self.starting_capital = starting_capital or float(
            os.getenv("STARTING_CAPITAL", "10000.00")
        )
        self._cash: float = self.starting_capital
        self._positions: dict[str, "Position"] = {}
        self._closed_trades: list["Trade"] = []
        self._peak_value: float = self.starting_capital
        self._consecutive_losses: int = 0

    # ── Read ────────────────────────────────────────────────────────────────

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def invested_value(self) -> float:
        return sum(p.market_value for p in self._positions.values())

    @property
    def total_value(self) -> float:
        return self._cash + self.invested_value

    @property
    def realized_pnl(self) -> float:
        return self.total_value - self.starting_capital - self.unrealized_pnl

    @property
    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self._positions.values())

    @property
    def total_pnl(self) -> float:
        return self.total_value - self.starting_capital

    @property
    def total_pnl_pct(self) -> float:
        return self.total_pnl / self.starting_capital

    @property
    def drawdown_pct(self) -> float:
        if self._peak_value == 0:
            return 0.0
        return max(0.0, (self._peak_value - self.total_value) / self._peak_value)

    @property
    def open_positions(self) -> dict[str, "Position"]:
        return dict(self._positions)

    @property
    def open_positions_count(self) -> int:
        return len(self._positions)

    @property
    def total_exposure_usd(self) -> float:
        return self.invested_value

    @property
    def consecutive_losses(self) -> int:
        return self._consecutive_losses

    @property
    def win_count(self) -> int:
        return sum(1 for t in self._closed_trades if t.realized_pnl > 0)

    @property
    def loss_count(self) -> int:
        return sum(1 for t in self._closed_trades if t.realized_pnl <= 0)

    @property
    def closed_trades(self) -> list["Trade"]:
        return list(self._closed_trades)

    def snapshot(self) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            timestamp=datetime.now(timezone.utc),
            total_value=self.total_value,
            cash=self._cash,
            invested=self.invested_value,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=self.unrealized_pnl,
            drawdown_pct=self.drawdown_pct,
            open_positions_count=self.open_positions_count,
            win_count=self.win_count,
            loss_count=self.loss_count,
        )

    # ── Mutate ──────────────────────────────────────────────────────────────

    def open_position(self, position: "Position") -> None:
        """Register a new open position and deduct cash."""
        if position.position_id in self._positions:
            raise ValueError(
                f"Position {position.position_id} already open"
            )
        cost = position.entry_price * position.shares
        if cost > self._cash:
            raise ValueError(
                f"Insufficient cash: need ${cost:.2f}, have ${self._cash:.2f}"
            )
        self._cash -= cost
        self._positions[position.position_id] = position

    def update_position_price(self, position_id: str, current_price: float) -> None:
        """Update mark-to-market price for an open position."""
        if position_id not in self._positions:
            return
        from datetime import datetime, timezone
        self._positions[position_id].current_price = current_price
        self._positions[position_id].last_updated = datetime.now(timezone.utc)
        if self.total_value > self._peak_value:
            self._peak_value = self.total_value

    def close_position(
        self,
        position_id: str,
        close_price: float,
        trade: "Trade",
    ) -> float:
        """Remove position, credit cash, record realized PnL."""
        if position_id not in self._positions:
            raise KeyError(f"Position {position_id} not found")

        pos = self._positions.pop(position_id)
        proceed = close_price * pos.shares
        self._cash += proceed

        pnl = trade.realized_pnl
        if pnl <= 0:
            self._consecutive_losses += 1
        else:
            self._consecutive_losses = 0

        self._closed_trades.append(trade)
        if self.total_value > self._peak_value:
            self._peak_value = self.total_value

        return pnl

    def partial_close_position(
        self, position_id: str, close_price: float, shares_to_close: int
    ) -> float:
        """Close a fraction of a position."""
        if position_id not in self._positions:
            raise KeyError(f"Position {position_id} not found")

        pos = self._positions[position_id]
        if shares_to_close <= 0:
            raise ValueError(
                f"shares_to_close must be positive, got {shares_to_close}"
            )
        if shares_to_close >= pos.shares:
            raise ValueError("Use close_position for full close")

        proceeds = close_price * shares_to_close
        self._cash += proceeds
        pos.shares -= shares_to_close
        pos.partial_tp_triggered = True

        if pos.direction.value == "LONG":
            pnl = (close_price - pos.entry_price) * shares_to_close
        else:
            pnl = (pos.entry_price - close_price) * shares_to_close

        return pnl
