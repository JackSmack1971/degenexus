"""Tests for quant proposal validation."""

import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError

from src.agents.quant_agent import QuantAgent
from src.models.signals import (
    TradeProposal, MarketSignal, EntryZone, IndicatorSnapshot,
    Trend, SignalStrength,
)


def _make_signal(direction: str = "LONG", price: float = 100.0) -> MarketSignal:
    low = max(0.001, price * 0.99)
    high = max(0.002, price * 1.01)
    inv = max(0.001, price * 0.95)
    return MarketSignal(
        symbol="TEST",
        direction=direction,
        trend=Trend.BULLISH,
        entry_zone=EntryZone(low=low, high=high),
        indicators=IndicatorSnapshot(),
        confidence=0.7,
        signal_strength=SignalStrength.MODERATE,
        reasoning="test",
        invalidation_level=inv,
        current_price=price,
    )


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


# ── _fallback_proposal tests ──────────────────────────────────────────────────

class TestFallbackProposal:

    def test_long_directional_arithmetic(self):
        sig = _make_signal("LONG", price=100.0)
        p = QuantAgent()._fallback_proposal(sig, portfolio_value=10_000, available_cash=5_000)
        assert p is not None
        assert p.stop_loss < p.entry_price, "LONG: stop_loss must be below entry"
        assert p.take_profit > p.entry_price, "LONG: take_profit must be above entry"
        assert p.risk_reward_ratio == 2.0

    def test_short_directional_arithmetic(self):
        sig = _make_signal("SHORT", price=100.0)
        p = QuantAgent()._fallback_proposal(sig, portfolio_value=10_000, available_cash=5_000)
        assert p is not None
        assert p.stop_loss > p.entry_price, "SHORT: stop_loss must be above entry"
        assert p.take_profit < p.entry_price, "SHORT: take_profit must be below entry"
        assert p.risk_reward_ratio == 2.0

    def test_zero_price_returns_none(self):
        sig = _make_signal(price=100.0)
        sig.current_price = 0.0
        assert QuantAgent()._fallback_proposal(sig, 10_000, 5_000) is None

    def test_negative_price_returns_none(self):
        sig = _make_signal(price=100.0)
        sig.current_price = -1.0
        assert QuantAgent()._fallback_proposal(sig, 10_000, 5_000) is None

    def test_insufficient_cash_returns_none(self):
        # price=150, available_cash=1: int(1*0.15/150)=0 → shares=0 → None
        sig = _make_signal(price=150.0)
        assert QuantAgent()._fallback_proposal(sig, 100_000, available_cash=1.0) is None

    def test_min_one_share_guaranteed_by_kelly_floor(self):
        # portfolio_value=1000, price=1000: max_loss_budget=10, risk/share=15
        # int(10/15)=0 → max(1,0)=1; available_cash=10000 → int(10000*0.15/1000)=1 → min(1,1)=1
        sig = _make_signal("LONG", price=1_000.0)
        p = QuantAgent()._fallback_proposal(sig, portfolio_value=1_000, available_cash=10_000)
        assert p is not None
        assert p.position_size_shares == 1

    def test_proposal_fields_are_consistent(self):
        sig = _make_signal("LONG", price=100.0)
        p = QuantAgent()._fallback_proposal(sig, portfolio_value=10_000, available_cash=5_000)
        assert p is not None
        assert p.position_value_usd == round(p.entry_price * p.position_size_shares, 2)
        assert p.max_loss_usd == round(p.entry_price * 0.015 * p.position_size_shares, 2)
        assert p.proposal_hash != ""


# ── design_proposal() success/failure paths (lines 58-66) ────────────────────

class TestDesignProposalPath:

    def test_design_proposal_success_returns_trade_proposal(self, valid_signal):
        """Lines 58-61: LLM call succeeds → _parse_proposal returns TradeProposal."""
        agent = QuantAgent()
        mock_response = {
            "entry_type": "LIMIT",
            "entry_price": 150.0,
            "stop_loss": 147.5,
            "take_profit": 155.0,
            "position_size_shares": 5,
            "position_value_usd": 750.0,
            "max_loss_usd": 12.5,
            "max_loss_pct": 0.00125,
            "risk_reward_ratio": 2.0,
            "portfolio_exposure_pct": 0.075,
            "reasoning": "Kelly sizing test",
        }
        agent.call_llm = MagicMock(return_value=mock_response)
        result = agent.design_proposal(valid_signal, portfolio_value=10_000.0, available_cash=5_000.0)
        assert result is not None
        assert result.entry_price == pytest.approx(150.0)
        agent.call_llm.assert_called_once()

    def test_design_proposal_exception_uses_fallback(self, valid_signal):
        """Lines 62-66: exception in try block → _fallback_proposal returned."""
        agent = QuantAgent()
        agent.call_llm = MagicMock(side_effect=RuntimeError("LLM exploded"))
        result = agent.design_proposal(valid_signal, portfolio_value=10_000.0, available_cash=5_000.0)
        assert result is not None

    def test_design_proposal_zero_portfolio_falls_back_to_none(self):
        """Lines 62-66: zero portfolio_value → fallback_proposal returns None (price=0 guard)."""
        sig = _make_signal("LONG", price=100.0)
        sig.current_price = 0.0
        agent = QuantAgent()
        agent.call_llm = MagicMock(side_effect=RuntimeError("LLM fail"))
        result = agent.design_proposal(sig, portfolio_value=0.0, available_cash=0.0)
        assert result is None


# ── _parse_proposal() success path (lines 134-135) ───────────────────────────

class TestParseProposalSuccess:

    def test_valid_long_response_returns_proposal_with_hash(self, valid_signal):
        """Lines 134-135: valid response → TradeProposal with proposal_hash set."""
        agent = QuantAgent()
        response = {
            "entry_type": "LIMIT",
            "entry_price": 150.0,
            "stop_loss": 147.5,
            "take_profit": 155.0,
            "position_size_shares": 5,
            "position_value_usd": 750.0,
            "max_loss_usd": 12.5,
            "max_loss_pct": 0.00125,
            "risk_reward_ratio": 2.0,
            "portfolio_exposure_pct": 0.075,
            "reasoning": "valid Kelly sizing",
        }
        proposal = agent._parse_proposal(response, valid_signal, portfolio_value=10_000.0)
        assert proposal is not None
        assert proposal.entry_price == pytest.approx(150.0)
        assert proposal.proposal_hash is not None
        assert proposal.stop_loss == pytest.approx(147.5)

    def test_missing_required_key_returns_none(self, valid_signal):
        """Lines 136-138: KeyError for missing required key → returns None."""
        agent = QuantAgent()
        result = agent._parse_proposal({}, valid_signal, portfolio_value=10_000.0)
        assert result is None

    def test_non_numeric_entry_price_returns_none(self, valid_signal):
        """Lines 136-138: ValueError from float('bad') → returns None."""
        agent = QuantAgent()
        response = {
            "entry_type": "LIMIT",
            "entry_price": "not_a_float",
            "stop_loss": 147.5,
            "take_profit": 155.0,
            "position_size_shares": 5,
            "position_value_usd": 750.0,
            "max_loss_usd": 12.5,
            "max_loss_pct": 0.00125,
            "risk_reward_ratio": 2.0,
            "portfolio_exposure_pct": 0.075,
        }
        result = agent._parse_proposal(response, valid_signal, portfolio_value=10_000.0)
        assert result is None


# ── _fallback() dict return (line 183) ───────────────────────────────────────

class TestQuantFallbackMethod:

    def test_fallback_returns_limit_entry_dict(self):
        """Line 183: _fallback() returns the LIMIT fallback dict."""
        agent = QuantAgent()
        result = agent._fallback("context string")
        assert result["entry_type"] == "LIMIT"
        assert "[FALLBACK]" in result["reasoning"]

    def test_fallback_called_when_client_none(self, valid_signal):
        """call_llm with client=None → _fallback() dict is returned by call_llm."""
        agent = QuantAgent()
        # _TestAgent bypasses init; QuantAgent() has _client=None (no API key)
        assert agent._client is None
        raw = agent.call_llm("sys", "ctx")
        assert raw["entry_type"] == "LIMIT"
