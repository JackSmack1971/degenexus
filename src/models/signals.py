"""Market signal, trade proposal, and risk decision schemas."""

from __future__ import annotations
from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator
import uuid
import hashlib
import json

from .trade import Direction

if TYPE_CHECKING:
    from .messages import AgentID


class Trend(str, Enum):
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    VOLATILE = "VOLATILE"


class SignalStrength(str, Enum):
    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"


class BBPosition(str, Enum):
    ABOVE_UPPER = "ABOVE_UPPER"
    UPPER = "UPPER"
    MID = "MID"
    LOWER = "LOWER"
    BELOW_LOWER = "BELOW_LOWER"


class DataQuality(str, Enum):
    LIVE = "LIVE"
    STALE = "STALE"
    SYNTHETIC = "SYNTHETIC"


class IndicatorSnapshot(BaseModel):
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    bb_position: Optional[BBPosition] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    volume_ratio: Optional[float] = None
    atr_14: Optional[float] = None


class EntryZone(BaseModel):
    low: float
    high: float


class MarketSignal(BaseModel):
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    timeframe: str = "1d"
    direction: Direction

    @field_validator("direction", mode="before")
    @classmethod
    def _normalise_direction(cls, v: object) -> str:
        return str(v).upper()
    trend: Trend
    entry_zone: EntryZone
    indicators: IndicatorSnapshot
    confidence: float = Field(ge=0.0, le=1.0)
    signal_strength: SignalStrength
    reasoning: str
    invalidation_level: float
    data_quality: DataQuality = DataQuality.LIVE
    market_context: str = ""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    current_price: float = 0.0


class TradeProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    signal_id: str
    symbol: str
    direction: Direction

    @field_validator("direction", mode="before")
    @classmethod
    def _normalise_direction(cls, v: object) -> str:
        return str(v).upper()
    entry_type: str = "LIMIT"
    entry_price: float = Field(gt=0)
    stop_loss: float = Field(gt=0)
    take_profit: float = Field(gt=0)
    position_size_shares: int = Field(ge=1)
    position_value_usd: float = Field(gt=0)
    max_loss_usd: float = Field(gt=0)
    max_loss_pct: float = Field(gt=0, le=1)
    risk_reward_ratio: float = Field(gt=0)
    portfolio_exposure_pct: float = Field(gt=0, le=1)
    time_in_force: str = "GTC"
    expiry_bars: int = 12
    reasoning: str
    proposal_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_hash(self) -> str:
        canonical = {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "position_size_shares": self.position_size_shares,
        }
        return hashlib.sha256(
            json.dumps(canonical, sort_keys=True).encode()
        ).hexdigest()

    def model_post_init(self, __context: object) -> None:
        if not self.proposal_hash:
            self.proposal_hash = self.compute_hash()

    @model_validator(mode="after")
    def validate_trade_levels(self) -> "TradeProposal":
        if self.direction == Direction.LONG:
            if not (self.stop_loss < self.entry_price < self.take_profit):
                raise ValueError("LONG proposals must satisfy stop_loss < entry_price < take_profit")
        else:
            if not (self.stop_loss > self.entry_price > self.take_profit):
                raise ValueError("SHORT proposals must satisfy stop_loss > entry_price > take_profit")
        return self


class RiskDecisionType(str, Enum):
    APPROVED = "APPROVED"
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS"
    REJECTED_HARD_RULE = "REJECTED_HARD_RULE"
    REJECTED_CONTEXTUAL = "REJECTED_CONTEXTUAL"
    REJECTED_EXPIRED = "REJECTED_EXPIRED"


class RiskDecision(BaseModel):
    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    proposal_hash: str
    approved: bool
    decision_type: RiskDecisionType
    hard_rules_passed: bool
    hard_rule_violations: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)
    risk_score: float = Field(ge=0.0, le=10.0, default=0.0)
    risk_reasoning: str
    expires_at: datetime
    signed_by: str = "RISK_MANAGER"

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

    def is_valid_for(self, proposal: TradeProposal) -> bool:
        return (
            self.proposal_hash == proposal.proposal_hash
            and not self.is_expired
            and self.approved
        )


class Challenge(BaseModel):
    challenge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    challenger: str
    challenged_agent: str
    disputed_field: str
    current_value: object
    suggested_value: object
    evidence: list[str]
    reasoning: str
    round_number: int = 1


class ChallengeResponse(BaseModel):
    challenge_id: str
    responder: str
    accepted: bool
    revised_value: Optional[object] = None
    counter_evidence: list[str] = Field(default_factory=list)
    reasoning: str
