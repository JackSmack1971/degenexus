"""Trade, position, and fill data models."""

from __future__ import annotations
from enum import Enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class TradeState(str, Enum):
    PROPOSED = "PROPOSED"
    RISK_REVIEWED = "RISK_REVIEWED"
    CEO_APPROVED = "CEO_APPROVED"
    QUEUED = "QUEUED"
    FILLED = "FILLED"
    OPEN = "OPEN"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    DROPPED = "DROPPED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = {TradeState.CLOSED, TradeState.REJECTED, TradeState.DROPPED, TradeState.CANCELLED}


class Direction(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class CloseReason(str, Enum):
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    PARTIAL_TP = "PARTIAL_TP"
    EXPIRY = "EXPIRY"
    MANUAL = "MANUAL"
    SYSTEM_HALT = "SYSTEM_HALT"


class Fill(BaseModel):
    fill_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trade_id: str
    symbol: str
    direction: Direction
    order_type: OrderType
    requested_price: float
    fill_price: float
    slippage_pct: float
    shares: int
    gross_value: float
    commission: float = 0.0
    status: str = "FILLED"
    fill_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Position(BaseModel):
    position_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trade_id: str
    symbol: str
    direction: Direction
    shares: int
    entry_price: float
    current_price: float = 0.0
    stop_loss: float
    take_profit: float
    partial_tp_triggered: bool = False
    opened_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def cost_basis(self) -> float:
        return self.entry_price * self.shares

    @property
    def market_value(self) -> float:
        return self.current_price * self.shares

    @property
    def unrealized_pnl(self) -> float:
        if self.direction == Direction.LONG:
            return (self.current_price - self.entry_price) * self.shares
        return (self.entry_price - self.current_price) * self.shares

    @property
    def unrealized_pnl_pct(self) -> float:
        if self.cost_basis == 0:
            return 0.0
        return self.unrealized_pnl / self.cost_basis


class Trade(BaseModel):
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    signal_id: str
    symbol: str
    direction: Direction
    state: TradeState = TradeState.PROPOSED
    order_type: OrderType = OrderType.LIMIT

    # Entry
    entry_price: float = 0.0
    fill_price: float = 0.0
    slippage_pct: float = 0.0
    shares: int = 0
    gross_value: float = 0.0

    # Risk levels
    stop_loss: float = 0.0
    take_profit: float = 0.0
    max_loss_usd: float = 0.0
    risk_reward_ratio: float = 0.0

    # Close
    close_price: float = 0.0
    close_shares: int = 0
    close_reason: Optional[CloseReason] = None
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0

    # Metadata
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    risk_score: float = 0.0
    agent_reasoning: dict = Field(default_factory=dict)

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    @property
    def is_winner(self) -> Optional[bool]:
        if self.state != TradeState.CLOSED:
            return None
        return self.realized_pnl > 0
