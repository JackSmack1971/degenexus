"""Tests for quant proposal validation."""

import pytest
from pydantic import ValidationError

from src.agents.quant_agent import QuantAgent
from src.models.signals import TradeProposal


def test_trade_proposal_rejects_inverted_long_levels(valid_signal):
    with pytest.raises(ValidationError, match="stop_loss < entry_price < take_profit"):
        TradeProposal(
            signal_id=valid_signal.signal_id,
            symbol=valid_signal.symbol,
            direction="LONG",
            entry_type="LIMIT",
            entry_price=100.0,
            stop_loss=110.0,
            take_profit=90.0,
            position_size_shares=10,
            position_value_usd=1000.0,
            max_loss_usd=100.0,
            max_loss_pct=0.01,
            risk_reward_ratio=2.0,
            portfolio_exposure_pct=0.10,
            reasoning="invalid levels",
        )


def test_parse_proposal_rejects_negative_entry_price(valid_signal):
    agent = QuantAgent()

    response = {
        "entry_type": "LIMIT",
        "entry_price": -5.0,
        "stop_loss": 145.0,
        "take_profit": 155.0,
        "position_size_shares": 10,
        "position_value_usd": 1500.0,
        "max_loss_usd": 25.0,
        "max_loss_pct": 0.0025,
        "risk_reward_ratio": 2.0,
        "portfolio_exposure_pct": 0.15,
        "reasoning": "bad entry",
    }

    proposal = agent._parse_proposal(response, valid_signal, portfolio_value=10_000.0)

    assert proposal is None


def test_parse_proposal_rejects_zero_shares(valid_signal):
    agent = QuantAgent()

    response = {
        "entry_type": "LIMIT",
        "entry_price": 150.0,
        "stop_loss": 147.5,
        "take_profit": 155.0,
        "position_size_shares": 0,
        "position_value_usd": 0.0,
        "max_loss_usd": 0.0,
        "max_loss_pct": 0.0,
        "risk_reward_ratio": 2.0,
        "portfolio_exposure_pct": 0.0,
        "reasoning": "zero size",
    }

    proposal = agent._parse_proposal(response, valid_signal, portfolio_value=10_000.0)

    assert proposal is None


def test_parse_proposal_rejects_inverted_short_levels(valid_signal):
    agent = QuantAgent()
    valid_signal.direction = "SHORT"

    response = {
        "entry_type": "LIMIT",
        "entry_price": 150.0,
        "stop_loss": 145.0,
        "take_profit": 155.0,
        "position_size_shares": 10,
        "position_value_usd": 1500.0,
        "max_loss_usd": 25.0,
        "max_loss_pct": 0.0025,
        "risk_reward_ratio": 2.0,
        "portfolio_exposure_pct": 0.15,
        "reasoning": "bad short levels",
    }

    proposal = agent._parse_proposal(response, valid_signal, portfolio_value=10_000.0)

    assert proposal is None
