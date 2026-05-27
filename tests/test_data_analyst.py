"""Tests for DataAnalystAgent signal parsing, fallback, and quality detection."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

from src.agents.data_analyst import DataAnalystAgent
from src.data.indicators import IndicatorEngine
from src.data.market_feed import OHLCVBar
from src.models.signals import DataQuality, MarketSignal
from src.models.trade import Direction


def _make_bars(n: int, symbol: str = "AAPL", source: str = "LIVE") -> list[OHLCVBar]:
    now = datetime.now(timezone.utc)
    bars = []
    for i in range(n):
        price = 150.0 + i * 0.1
        bars.append(OHLCVBar(
            symbol=symbol,
            timestamp=now - timedelta(days=n - i),
            open=price - 0.5,
            high=price + 1.0,
            low=price - 1.0,
            close=price,
            volume=1_000_000.0,
            source=source,
        ))
    return bars


def _make_agent():
    """Create a DataAnalystAgent using the DI constructor (no __new__ workaround)."""
    fake_feed = MagicMock()
    fake_feed.fetch.return_value = []
    return DataAnalystAgent(feed=fake_feed, engine=IndicatorEngine())


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


class TestDIConstructor:
    """Verify DI constructor replaces __new__ workaround — issue #69."""

    def test_constructor_accepts_feed_kwarg(self):
        fake_feed = MagicMock()
        agent = DataAnalystAgent(feed=fake_feed)
        assert agent.feed is fake_feed

    def test_constructor_accepts_engine_kwarg(self):
        engine = IndicatorEngine()
        agent = DataAnalystAgent(engine=engine)
        assert agent.engine is engine

    def test_constructor_defaults_when_not_injected(self):
        agent = DataAnalystAgent()
        assert agent.feed is not None
        assert agent.engine is not None

    def test_performance_context_still_works(self):
        fake_feed = MagicMock()
        agent = DataAnalystAgent("ctx123", feed=fake_feed)
        assert agent.performance_context == "ctx123"


class TestAnalyzeMethod:
    """Tests for analyze() — previously unreachable without DI (issue #69 coverage gap)."""

    def test_analyze_with_sufficient_bars_returns_market_signal(self):
        """≥30 bars + valid LLM response → MarketSignal returned."""
        bars = _make_bars(35, source="LIVE")
        fake_feed = MagicMock()
        fake_feed.fetch.return_value = bars
        fake_engine = MagicMock()
        fake_engine.compute_all.return_value = {"rsi_14": 52.0}

        agent = DataAnalystAgent(feed=fake_feed, engine=fake_engine)
        agent.call_llm = MagicMock(return_value=VALID_RESPONSE)

        result = agent.analyze("AAPL")
        assert isinstance(result, MarketSignal)
        assert result.symbol == "AAPL"
        assert result.data_quality == DataQuality.LIVE

    def test_analyze_with_fewer_than_30_bars_returns_none(self):
        """<30 bars → logger.warning + return None (lines 42-43 of data_analyst.py)."""
        bars = _make_bars(20)
        fake_feed = MagicMock()
        fake_feed.fetch.return_value = bars

        agent = DataAnalystAgent(feed=fake_feed)
        result = agent.analyze("AAPL")
        assert result is None

    def test_analyze_with_exactly_30_bars_boundary_proceeds(self):
        """BVA: exactly 30 bars is the minimum — should NOT trigger the <30 guard."""
        bars = _make_bars(30, source="LIVE")
        fake_feed = MagicMock()
        fake_feed.fetch.return_value = bars
        fake_engine = MagicMock()
        fake_engine.compute_all.return_value = {}

        agent = DataAnalystAgent(feed=fake_feed, engine=fake_engine)
        agent.call_llm = MagicMock(return_value=VALID_RESPONSE)

        result = agent.analyze("AAPL")
        assert result is not None

    def test_analyze_with_feed_exception_returns_none(self):
        """feed.fetch() raises → outer except catches → returns None (lines 59-61)."""
        fake_feed = MagicMock()
        fake_feed.fetch.side_effect = RuntimeError("network error")

        agent = DataAnalystAgent(feed=fake_feed)
        result = agent.analyze("AAPL")
        assert result is None

    def test_analyze_sets_synthetic_quality_on_synthetic_bars(self):
        """Any bar with source='SYNTHETIC' → data_quality=DataQuality.SYNTHETIC."""
        bars = _make_bars(35, source="SYNTHETIC")
        fake_feed = MagicMock()
        fake_feed.fetch.return_value = bars
        fake_engine = MagicMock()
        fake_engine.compute_all.return_value = {}

        agent = DataAnalystAgent(feed=fake_feed, engine=fake_engine)
        agent.call_llm = MagicMock(return_value=VALID_RESPONSE)

        result = agent.analyze("AAPL")
        assert result is not None
        assert result.data_quality == DataQuality.SYNTHETIC

    def test_analyze_with_empty_bars_returns_none(self):
        """Empty bar list (0 bars) → <30 guard → returns None."""
        fake_feed = MagicMock()
        fake_feed.fetch.return_value = []

        agent = DataAnalystAgent(feed=fake_feed)
        result = agent.analyze("AAPL")
        assert result is None


class TestBuildBarSummary:
    """Tests for _build_bar_summary() — previously unreachable without DI (issue #69)."""

    def test_returns_string_with_symbol(self):
        """_build_bar_summary with 10 bars returns string containing SYMBOL header."""
        bars = _make_bars(10, symbol="AAPL")
        agent = DataAnalystAgent()
        result = agent._build_bar_summary(bars, {})
        assert "SYMBOL: AAPL" in result

    def test_returns_string_with_current_price(self):
        """String contains CURRENT PRICE formatted to 4 decimal places."""
        bars = _make_bars(10)
        agent = DataAnalystAgent()
        result = agent._build_bar_summary(bars, {"rsi_14": 52.1234})
        assert "CURRENT PRICE:" in result
        assert "rsi_14" in result

    def test_none_indicator_values_excluded(self):
        """None indicator values are filtered out of the summary."""
        bars = _make_bars(10)
        agent = DataAnalystAgent()
        result = agent._build_bar_summary(bars, {"rsi_14": None, "volume_ratio": 1.5})
        assert "rsi_14" not in result
        assert "volume_ratio" in result

    def test_empty_bars_list_returns_unknown_symbol(self):
        """Empty bars list → SYMBOL: UNKNOWN (guards bars[-1] access)."""
        agent = DataAnalystAgent()
        result = agent._build_bar_summary([], {})
        assert "SYMBOL: UNKNOWN" in result


class TestParseSignalEntryZoneNonDict:
    """Line 115 — entry_zone is not a dict → fallback to current_price band."""

    def test_float_entry_zone_uses_price_band(self):
        """LLM hallucination: entry_zone=150.0 (float, not dict) → band from current_price."""
        agent = _make_agent()
        response = {**VALID_RESPONSE, "entry_zone": 150.0}
        sig = agent._parse_signal(response, "AAPL", 200.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.entry_zone.low == pytest.approx(200.0 * 0.995)
        assert sig.entry_zone.high == pytest.approx(200.0 * 1.005)

    def test_list_entry_zone_uses_price_band(self):
        """entry_zone=[149, 151] (list, not dict) → band from current_price."""
        agent = _make_agent()
        response = {**VALID_RESPONSE, "entry_zone": [149.0, 151.0]}
        sig = agent._parse_signal(response, "AAPL", 200.0, {}, DataQuality.LIVE)
        assert sig is not None
        assert sig.entry_zone.low == pytest.approx(200.0 * 0.995)
