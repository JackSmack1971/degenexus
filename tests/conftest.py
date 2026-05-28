"""Shared test fixtures."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.signals import (
    MarketSignal, TradeProposal, RiskDecision, RiskDecisionType,
    IndicatorSnapshot, EntryZone, Trend, SignalStrength, DataQuality,
)
from src.models.trade import Position, Direction
from src.core.portfolio import Portfolio
from src.core.risk_gate import RiskGate, RiskLimits
from src.core.slippage import SlippageModel
from src.core.trade_lifecycle import TradeLifecycle
from datetime import datetime, timezone, timedelta
import uuid


@pytest.fixture
def limits():
    return RiskLimits(
        max_loss_pct_per_trade=0.02,
        max_open_positions=5,
        max_total_exposure_pct=0.80,
        max_consecutive_losses=3,
        min_risk_reward=1.5,
        min_confidence=0.55,
    )


@pytest.fixture
def risk_gate(limits):
    return RiskGate(limits=limits)


@pytest.fixture
def portfolio():
    return Portfolio(starting_capital=10_000.0)


@pytest.fixture
def slippage():
    return SlippageModel(seed=42)


@pytest.fixture
def lifecycle():
    return TradeLifecycle()


@pytest.fixture
def valid_signal():
    return MarketSignal(
        symbol="AAPL",
        direction="LONG",
        trend=Trend.BULLISH,
        entry_zone=EntryZone(low=149.50, high=150.50),
        indicators=IndicatorSnapshot(rsi_14=52.3, macd_signal=0.23, volume_ratio=1.4),
        confidence=0.72,
        signal_strength=SignalStrength.MODERATE,
        reasoning="RSI recovering, MACD bullish, volume above average",
        invalidation_level=147.0,
        data_quality=DataQuality.LIVE,
        current_price=150.0,
    )


@pytest.fixture
def valid_proposal(valid_signal):
    p = TradeProposal(
        signal_id=valid_signal.signal_id,
        symbol="AAPL",
        direction="LONG",
        entry_type="LIMIT",
        entry_price=150.0,
        stop_loss=147.5,
        take_profit=155.0,
        position_size_shares=10,
        position_value_usd=1500.0,
        max_loss_usd=25.0,
        max_loss_pct=0.0025,
        risk_reward_ratio=2.0,
        portfolio_exposure_pct=0.15,
        time_in_force="GTC",
        expiry_bars=12,
        reasoning="Kelly 0.5x: 10 shares. R:R 2:1.",
    )
    p.proposal_hash = p.compute_hash()
    return p


@pytest.fixture
def valid_risk_decision(valid_proposal):
    return RiskDecision(
        proposal_id=valid_proposal.proposal_id,
        proposal_hash=valid_proposal.proposal_hash,
        approved=True,
        decision_type=RiskDecisionType.APPROVED,
        hard_rules_passed=True,
        risk_score=3.0,
        risk_reasoning="All rules pass, good R:R",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
    )


@pytest.fixture
def open_position(valid_proposal):
    return Position(
        trade_id=str(uuid.uuid4()),
        symbol="AAPL",
        direction=Direction.LONG,
        shares=10,
        entry_price=150.0,
        current_price=150.0,
        stop_loss=147.5,
        take_profit=155.0,
    )
