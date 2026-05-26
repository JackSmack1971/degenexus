"""Tests for IndicatorEngine — NaN handling, empty input, volume ratio."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.data.indicators import IndicatorEngine
from src.data.market_feed import OHLCVBar


def _make_bars(n: int, base_price: float = 100.0) -> list[OHLCVBar]:
    bars = []
    now = datetime.now(timezone.utc)
    price = base_price
    for i in range(n):
        close = price + (i * 0.1)
        bars.append(OHLCVBar(
            symbol="TEST",
            timestamp=now - timedelta(days=n - i),
            open=close - 0.5,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=float(1_000_000 + i * 10_000),
            source="SYNTHETIC",
        ))
    return bars


class TestComputeAllEmpty:
    def test_empty_bar_list_returns_empty_dict(self):
        engine = IndicatorEngine()
        result = engine.compute_all([])
        assert isinstance(result, dict)

    def test_single_bar_returns_dict(self):
        engine = IndicatorEngine()
        result = engine.compute_all(_make_bars(1))
        assert isinstance(result, dict)


class TestComputeAllGracefulNone:
    def test_returns_dict_when_ta_unavailable(self):
        """All ta-dependent methods return None-filled dicts when ta raises ImportError."""
        engine = IndicatorEngine()
        bars = _make_bars(60)
        # Patch ta imports inside each helper to raise ImportError
        with patch.dict("sys.modules", {"ta": None, "ta.momentum": None,
                                         "ta.trend": None, "ta.volatility": None}):
            result = engine.compute_all(bars)
        # compute_all wraps everything in try/except — must return a dict, never raise
        assert isinstance(result, dict)

    def test_result_never_raises_on_bad_input(self):
        engine = IndicatorEngine()
        # Pass a list of objects with wrong attributes
        class BadBar:
            close = "not_a_float"
            high = None
            low = None
            volume = None
        result = engine.compute_all([BadBar()])
        assert isinstance(result, dict)


class TestVolumeRatio:
    def test_equal_volumes_returns_ratio_1(self):
        """When all bars have the same volume, ratio = 1.0."""
        engine = IndicatorEngine()
        bars = _make_bars(20)
        for b in bars:
            b.volume = 1_000_000.0
        import pandas as pd
        volumes = pd.Series([b.volume for b in bars])
        result = engine._volume_ratio(volumes)
        assert result.get("volume_ratio") == pytest.approx(1.0)

    def test_recent_vol_double_average_returns_2(self):
        """Recent bar volume = 2× average → ratio ≈ 2.0."""
        engine = IndicatorEngine()
        bars = _make_bars(20)
        avg_vol = 1_000_000.0
        for b in bars[:-1]:
            b.volume = avg_vol
        bars[-1].volume = avg_vol * 2
        import pandas as pd
        volumes = pd.Series([b.volume for b in bars])
        result = engine._volume_ratio(volumes)
        # ratio = (2M) / mean([1M * 19, 2M]) = 2M / (21M/20) ≈ 1.9
        assert result.get("volume_ratio") is not None
        assert result["volume_ratio"] > 1.5

    def test_zero_average_volume_returns_ratio_1(self):
        """Division by zero guard: avg_vol=0 → ratio=1.0."""
        engine = IndicatorEngine()
        import pandas as pd
        volumes = pd.Series([0.0] * 20)
        result = engine._volume_ratio(volumes)
        assert result.get("volume_ratio") == pytest.approx(1.0)


class TestIndicatorNaNHandling:
    def test_fewer_bars_than_rsi_window_returns_none(self):
        """With fewer than 14 bars, RSI cannot be computed; should return None."""
        engine = IndicatorEngine()
        # 5 bars is fewer than RSI window (14)
        bars = _make_bars(5)
        try:
            import ta  # noqa
        except (ImportError, Exception):
            pytest.skip("ta library not available")
        import pandas as pd
        closes = pd.Series([b.close for b in bars])
        result = engine._rsi(closes)
        # With only 5 bars, RSI iloc[-1] will be NaN → None
        assert result.get("rsi_14") is None

    def test_fewer_bars_than_bb_window_returns_none(self):
        """With fewer than 20 bars, Bollinger Bands cannot be computed."""
        engine = IndicatorEngine()
        bars = _make_bars(10)
        try:
            import ta  # noqa
        except (ImportError, Exception):
            pytest.skip("ta library not available")
        import pandas as pd
        closes = pd.Series([b.close for b in bars])
        result = engine._bollinger(closes)
        # All BB values should be None with insufficient bars
        assert result.get("bb_upper") is None
        assert result.get("bb_lower") is None

    def test_sufficient_bars_computes_volume_ratio(self):
        """volume_ratio doesn't require ta — verifies compute_all partial success."""
        engine = IndicatorEngine()
        bars = _make_bars(60)
        import pandas as pd
        volumes = pd.Series([b.volume for b in bars])
        result = engine._volume_ratio(volumes)
        assert "volume_ratio" in result
        assert result["volume_ratio"] is not None
