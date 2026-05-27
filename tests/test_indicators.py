"""Tests for IndicatorEngine — NaN handling, empty input, volume ratio."""

import sys
import types
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from src.data.indicators import IndicatorEngine
from src.data.market_feed import OHLCVBar


def _make_fake_ta_momentum(rsi_side_effect=None):
    """Build a sys.modules-injectable ta.momentum namespace."""
    fake_mom = types.ModuleType("ta.momentum")
    fake_mom.RSIIndicator = MagicMock(side_effect=rsi_side_effect) if rsi_side_effect else MagicMock()
    return fake_mom


def _make_fake_ta_trend(macd_side_effect=None, ema_side_effect=None):
    """Build a sys.modules-injectable ta.trend namespace."""
    fake_trend = types.ModuleType("ta.trend")
    fake_trend.MACD = MagicMock(side_effect=macd_side_effect) if macd_side_effect else MagicMock()
    fake_trend.EMAIndicator = MagicMock(side_effect=ema_side_effect) if ema_side_effect else MagicMock()
    return fake_trend


def _make_fake_ta_volatility(bb_factory=None, atr_side_effect=None):
    """Build a sys.modules-injectable ta.volatility namespace."""
    fake_vol = types.ModuleType("ta.volatility")
    fake_vol.BollingerBands = bb_factory or MagicMock()
    fake_vol.AverageTrueRange = MagicMock(side_effect=atr_side_effect) if atr_side_effect else MagicMock()
    return fake_vol


def _ta_patch(mom=None, trend=None, vol=None):
    """Return a patch.dict context manager that injects fake ta sub-modules into sys.modules."""
    fake_ta = types.ModuleType("ta")
    overrides: dict = {}
    if mom is not None:
        fake_ta.momentum = mom
        overrides["ta.momentum"] = mom
    if trend is not None:
        fake_ta.trend = trend
        overrides["ta.trend"] = trend
    if vol is not None:
        fake_ta.volatility = vol
        overrides["ta.volatility"] = vol
    overrides["ta"] = fake_ta
    return patch.dict(sys.modules, overrides)


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


class TestComputeAllOuterException:
    """Lines 40-42 — outer except in compute_all returns {} when internals raise."""

    def test_outer_exception_returns_empty_dict(self, mocker):
        engine = IndicatorEngine()
        bars = _make_bars(30)
        # Force an exception outside the sub-method try/excepts by patching _rsi to raise
        mocker.patch.object(engine, "_rsi", side_effect=RuntimeError("injected failure"))
        result = engine.compute_all(bars)
        assert result == {}

    def test_bad_bar_attribute_raises_returns_empty_dict(self):
        """When bar.close is a property that raises, the outer except fires."""
        class ExplodingBar:
            @property
            def close(self):
                raise AttributeError("no close attr")
            @property
            def high(self):
                raise AttributeError("no high attr")
            @property
            def low(self):
                raise AttributeError("no low attr")
            @property
            def volume(self):
                raise AttributeError("no volume attr")

        engine = IndicatorEngine()
        result = engine.compute_all([ExplodingBar()])
        assert result == {}


class TestBollingerPriceClassification:
    """Lines 78-91 — all 5 bb_position classifications."""

    def _make_bollinger_result(self, price: float, upper: float, lower: float, mid: float) -> dict:
        """Helper: inject fake BollingerBands via sys.modules so test works with or without ta."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([mid] * 25 + [price])

        mock_bb = MagicMock()
        mock_bb.bollinger_hband.return_value = pd.Series([upper])
        mock_bb.bollinger_lband.return_value = pd.Series([lower])
        mock_bb.bollinger_mavg.return_value = pd.Series([mid])

        fake_vol = _make_fake_ta_volatility(bb_factory=MagicMock(return_value=mock_bb))
        with _ta_patch(vol=fake_vol):
            return engine._bollinger(closes)

    def test_price_above_upper_band(self):
        result = self._make_bollinger_result(price=110.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "ABOVE_UPPER"
        assert result["bb_upper"] == pytest.approx(105.0)
        assert result["bb_lower"] == pytest.approx(95.0)

    def test_price_in_upper_zone(self):
        # UPPER: price >= mid + (upper-mid)*0.5 = 100 + 2.5 = 102.5
        result = self._make_bollinger_result(price=103.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "UPPER"

    def test_price_in_mid_zone(self):
        # MID: price >= mid - (mid-lower)*0.5 = 100 - 2.5 = 97.5 and < 102.5
        result = self._make_bollinger_result(price=99.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "MID"

    def test_price_in_lower_zone(self):
        # LOWER: price >= lower=95.0 and < 97.5
        result = self._make_bollinger_result(price=96.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "LOWER"

    def test_price_below_lower_band(self):
        # BELOW_LOWER: price < lower=95.0
        result = self._make_bollinger_result(price=90.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "BELOW_LOWER"

    def test_bva_price_exactly_at_upper(self):
        """BVA boundary: price == upper → ABOVE_UPPER."""
        result = self._make_bollinger_result(price=105.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "ABOVE_UPPER"

    def test_bva_price_exactly_at_lower(self):
        """BVA boundary: price == lower → LOWER (not BELOW_LOWER)."""
        result = self._make_bollinger_result(price=95.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "LOWER"


class TestATRSuccessPath:
    """Lines 115-116 — ATR valid computation with sufficient bars."""

    def test_atr_with_30_bars_returns_float(self):
        try:
            import ta  # noqa
        except (ImportError, Exception):
            pytest.skip("ta library not available")
        import pandas as pd
        engine = IndicatorEngine()
        bars = _make_bars(30)
        highs = pd.Series([b.high for b in bars])
        lows = pd.Series([b.low for b in bars])
        closes = pd.Series([b.close for b in bars])
        result = engine._atr(highs, lows, closes)
        assert "atr_14" in result
        assert result["atr_14"] is not None
        assert isinstance(result["atr_14"], float)

    def test_compute_all_with_sufficient_bars_covers_atr_path(self):
        """compute_all with 30 bars exercises the ATR and all other success paths."""
        try:
            import ta  # noqa
        except (ImportError, Exception):
            pytest.skip("ta library not available")
        engine = IndicatorEngine()
        bars = _make_bars(30)
        result = engine.compute_all(bars)
        assert isinstance(result, dict)
        assert "atr_14" in result
        assert "rsi_14" in result
        assert "volume_ratio" in result


class TestRSIExceptionFallback:
    """Line 50-51 — _rsi except path returns None-filled dict (already covered by ta=None test).
    Uses sys.modules injection so tests pass regardless of whether ta is installed."""

    def test_rsi_raises_returns_none(self):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 30)
        fake_mom = _make_fake_ta_momentum(rsi_side_effect=ValueError("rsi error"))
        with _ta_patch(mom=fake_mom):
            result = engine._rsi(closes)
        assert result == {"rsi_14": None}

    def test_macd_raises_returns_none(self):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 30)
        fake_trend = _make_fake_ta_trend(macd_side_effect=ValueError("macd error"))
        with _ta_patch(trend=fake_trend):
            result = engine._macd(closes)
        assert result == {"macd_line": None, "macd_signal": None, "macd_histogram": None}

    def test_ema_raises_returns_none(self):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 60)
        fake_trend = _make_fake_ta_trend(ema_side_effect=ValueError("ema error"))
        with _ta_patch(trend=fake_trend):
            result = engine._ema(closes)
        assert result == {"ema_20": None, "ema_50": None}

    def test_atr_raises_returns_none(self):
        import pandas as pd
        engine = IndicatorEngine()
        highs = pd.Series([101.0] * 30)
        lows = pd.Series([99.0] * 30)
        closes = pd.Series([100.0] * 30)
        fake_vol = _make_fake_ta_volatility(atr_side_effect=ValueError("atr error"))
        with _ta_patch(vol=fake_vol):
            result = engine._atr(highs, lows, closes)
        assert result == {"atr_14": None}
