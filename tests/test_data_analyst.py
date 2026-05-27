"""Tests for DataAnalystAgent signal parsing, fallback, and quality detection."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from src.agents.data_analyst import DataAnalystAgent
from src.models.signals import DataQuality, MarketSignal
from src.models.trade import Direction


def _make_agent():
    agent = DataAnalystAgent.__new__(DataAnalystAgent)
    agent.agent_id = "DATA_ANALYST"
    agent.performance_context = ""
    agent._provider = "fallback"
    agent._client = None
    agent._llm_timeout_seconds = 30
    from src.data.indicators import IndicatorEngine
    agent.engine = IndicatorEngine()
    return agent


VALID_RESPONSE = {
    "direction": "LONG",
    "trend": "BULLISH",
    "confidence": 0.72,
    "signal_strength": "MODERATE",
    "entry_zone": {"low": 149.0, "high": 151.0},
    "invalidation_level": 145.0,
    "reasoning": "RSI=52, MACD bullish crossover",
    "market_context": "earnings approaching",
}


class TestParseSignalHappyPath:
    def test_returns_market_signal(self):
        agent = _make_agent()
        sig = agent._parse_signal(VALID_RESPONSE, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert isinstance(sig, MarketSignal)
        assert sig.symbol == "AAPL"
        assert sig.confidence == pytest.approx(0.72)
        assert sig.current_price == 150.0

    def test_data_quality_live_preserved(self):
        agent = _make_agent()
        sig = agent._parse_signal(VALID_RESPONSE, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig.data_quality == DataQuality.LIVE

    def test_data_quality_synthetic_preserved(self):
        agent = _make_agent()
        sig = agent._parse_signal(VALID_RESPONSE, "AAPL", 150.0, {}, DataQuality.SYNTHETIC)
        assert sig.data_quality == DataQuality.SYNTHETIC

    def test_entry_zone_from_response(self):
        agent = _make_agent()
        sig = agent._parse_signal(VALID_RESPONSE, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig.entry_zone.low == pytest.approx(149.0)
        assert sig.entry_zone.high == pytest.approx(151.0)

    def test_missing_entry_zone_defaults_to_current_price_band(self):
        agent = _make_agent()
        response = {**VALID_RESPONSE, "entry_zone": {}}
        sig = agent._parse_signal(response, "AAPL", 100.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.entry_zone.low == pytest.approx(100.0 * 0.995)
        assert sig.entry_zone.high == pytest.approx(100.0 * 1.005)


class TestDirectionTypeExplicit:
    """Regression for issue #68 — direction must be Direction enum in MarketSignal."""

    def test_short_direction_str_produces_direction_enum(self):
        """'SHORT' string from LLM response must yield Direction.SHORT, not a bare str."""
        agent = _make_agent()
        response = {**VALID_RESPONSE, "direction": "SHORT"}
        sig = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.direction == Direction.SHORT

    def test_long_direction_lowercase_coerces_to_enum(self):
        """Lowercase 'long' from LLM response must yield Direction.LONG after .upper()."""
        agent = _make_agent()
        response = {**VALID_RESPONSE, "direction": "long"}
        sig = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.direction == Direction.LONG

    def test_none_direction_returns_none_signal(self):
        """direction=None → str(None).upper()='NONE' → invalid Direction → _parse_signal returns None."""
        agent = _make_agent()
        response = {**VALID_RESPONSE, "direction": None}
        sig = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig is None


class TestParseSignalInvalidInputs:
    def test_invalid_direction_returns_none(self):
        agent = _make_agent()
        response = {**VALID_RESPONSE, "direction": "BUY"}
        result = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert result is None

    def test_invalid_trend_returns_none(self):
        agent = _make_agent()
        response = {**VALID_RESPONSE, "trend": "SIDEWAYS"}
        result = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert result is None

    def test_confidence_clamped_above_1(self):
        agent = _make_agent()
        response = {**VALID_RESPONSE, "confidence": 5.0}
        sig = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.confidence == pytest.approx(1.0)

    def test_confidence_clamped_below_0(self):
        agent = _make_agent()
        response = {**VALID_RESPONSE, "confidence": -1.0}
        sig = agent._parse_signal(response, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.confidence == pytest.approx(0.0)

    def test_empty_response_dict_returns_none_or_defaults(self):
        agent = _make_agent()
        # Empty response uses defaults: direction=LONG, trend=NEUTRAL — should succeed
        result = agent._parse_signal({}, "AAPL", 150.0, {}, DataQuality.LIVE)
        assert result is not None
        assert result.confidence == pytest.approx(0.5)


class TestFallback:
    def test_fallback_returns_dict_with_low_confidence(self):
        agent = _make_agent()
        result = agent._fallback("context")
        assert isinstance(result, dict)
        assert result["confidence"] == pytest.approx(0.45)
        assert result["direction"] == "LONG"

    def test_fallback_entry_zone_is_zero(self):
        agent = _make_agent()
        result = agent._fallback("context")
        assert result["entry_zone"]["low"] == 0
        assert result["entry_zone"]["high"] == 0

    def test_fallback_signal_produces_valid_market_signal_via_parse(self):
        """Verify fallback dict + _parse_signal produces a usable (low-confidence) signal."""
        agent = _make_agent()
        fb = agent._fallback("ctx")
        sig = agent._parse_signal(fb, "AAPL", 100.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.confidence == pytest.approx(0.45)
        assert sig.entry_zone.low == pytest.approx(0.0)


class TestSyntheticQualityDetection:
    def test_synthetic_bars_set_data_quality_synthetic(self):
        """Verify analyze() sets SYNTHETIC quality when any bar has source='SYNTHETIC'."""
        from src.data.market_feed import OHLCVBar
        agent = _make_agent()

        ts = datetime.now(timezone.utc)
        synthetic_bars = [
            OHLCVBar(
                timestamp=ts, symbol="TEST", open=100.0, high=101.0,
                low=99.0, close=100.5, volume=1000, source="SYNTHETIC"
            )
            for _ in range(35)
        ]

        captured = {}

        def fake_parse_signal(response, symbol, current_price, indicators, data_quality):
            captured["data_quality"] = data_quality
            return None

        agent.feed = MagicMock()
        agent.feed.fetch.return_value = synthetic_bars
        agent.engine = MagicMock()
        agent.engine.compute_all.return_value = {}
        agent._build_bar_summary = MagicMock(return_value="summary")
        agent.call_llm = MagicMock(return_value=VALID_RESPONSE)
        agent._parse_signal = fake_parse_signal

        agent.analyze("TEST")
        assert captured["data_quality"] == DataQuality.SYNTHETIC
