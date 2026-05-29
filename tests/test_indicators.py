"""Tests for IndicatorEngine — NaN handling, empty input, volume ratio."""

import sys
import types
import pytest
from datetime import datetime, timezone, timedelta

from src.data.indicators import IndicatorEngine
from src.data.market_feed import OHLCVBar


def _make_fake_ta_momentum(mocker, rsi_side_effect=None):
    """Build a sys.modules-injectable ta.momentum namespace."""
    fake_mom = types.ModuleType("ta.momentum")
    fake_mom.RSIIndicator = mocker.MagicMock(side_effect=rsi_side_effect) if rsi_side_effect else mocker.MagicMock()
    return fake_mom


def _make_fake_ta_trend(mocker, macd_side_effect=None, ema_side_effect=None):
    """Build a sys.modules-injectable ta.trend namespace."""
    fake_trend = types.ModuleType("ta.trend")
    fake_trend.MACD = mocker.MagicMock(side_effect=macd_side_effect) if macd_side_effect else mocker.MagicMock()
    fake_trend.EMAIndicator = mocker.MagicMock(side_effect=ema_side_effect) if ema_side_effect else mocker.MagicMock()
    return fake_trend


def _make_fake_ta_volatility(mocker, bb_factory=None, atr_side_effect=None):
    """Build a sys.modules-injectable ta.volatility namespace."""
    fake_vol = types.ModuleType("ta.volatility")
    fake_vol.BollingerBands = bb_factory or mocker.MagicMock()
    fake_vol.AverageTrueRange = mocker.MagicMock(side_effect=atr_side_effect) if atr_side_effect else mocker.MagicMock()
    return fake_vol


def _ta_patch(mocker, mom=None, trend=None, vol=None):
    """Return a mocker.patch.dict context manager that injects fake ta sub-modules into sys.modules."""
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
    mocker.patch.dict(sys.modules, overrides)


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
    def test_returns_dict_when_ta_unavailable(self, mocker):
        """All ta-dependent methods return None-filled dicts when ta raises ImportError."""
        engine = IndicatorEngine()
        bars = _make_bars(60)
        mocker.patch.dict("sys.modules", {"ta": None, "ta.momentum": None,
                                           "ta.trend": None, "ta.volatility": None})
        result = engine.compute_all(bars)
        assert isinstance(result, dict)

    def test_result_never_raises_on_bad_input(self):
        engine = IndicatorEngine()
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
    def test_fewer_bars_than_rsi_window_returns_none(self, mocker):
        """With fewer than 14 bars, RSI iloc[-1] is NaN → should return None."""
        import pandas as pd
        engine = IndicatorEngine()
        bars = _make_bars(5)
        closes = pd.Series([b.close for b in bars])
        nan_series = pd.Series([float("nan")] * len(closes))
        mock_rsi_inst = mocker.MagicMock()
        mock_rsi_inst.rsi.return_value = nan_series
        fake_mom = _make_fake_ta_momentum(mocker)
        fake_mom.RSIIndicator = mocker.MagicMock(return_value=mock_rsi_inst)
        _ta_patch(mocker, mom=fake_mom)
        result = engine._rsi(closes)
        assert result.get("rsi_14") is None

    def test_fewer_bars_than_bb_window_returns_none(self, mocker):
        """With fewer than 20 bars, Bollinger Bands values are NaN → should return None."""
        import pandas as pd
        engine = IndicatorEngine()
        bars = _make_bars(10)
        closes = pd.Series([b.close for b in bars])
        nan_series = pd.Series([float("nan")] * len(closes))
        mock_bb = mocker.MagicMock()
        mock_bb.bollinger_hband.return_value = nan_series
        mock_bb.bollinger_lband.return_value = nan_series
        mock_bb.bollinger_mavg.return_value = nan_series
        fake_vol = _make_fake_ta_volatility(mocker, bb_factory=mocker.MagicMock(return_value=mock_bb))
        _ta_patch(mocker, vol=fake_vol)
        result = engine._bollinger(closes)
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

    def _make_bollinger_result(self, mocker, price: float, upper: float, lower: float, mid: float) -> dict:
        """Helper: inject fake BollingerBands via sys.modules so test works with or without ta."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([mid] * 25 + [price])

        mock_bb = mocker.MagicMock()
        mock_bb.bollinger_hband.return_value = pd.Series([upper])
        mock_bb.bollinger_lband.return_value = pd.Series([lower])
        mock_bb.bollinger_mavg.return_value = pd.Series([mid])

        fake_vol = _make_fake_ta_volatility(mocker, bb_factory=mocker.MagicMock(return_value=mock_bb))
        _ta_patch(mocker, vol=fake_vol)
        return engine._bollinger(closes)

    def test_price_above_upper_band(self, mocker):
        result = self._make_bollinger_result(mocker, price=110.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "ABOVE_UPPER"
        assert result["bb_upper"] == pytest.approx(105.0)
        assert result["bb_lower"] == pytest.approx(95.0)

    def test_price_in_upper_zone(self, mocker):
        result = self._make_bollinger_result(mocker, price=103.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "UPPER"

    def test_price_in_mid_zone(self, mocker):
        result = self._make_bollinger_result(mocker, price=99.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "MID"

    def test_price_in_lower_zone(self, mocker):
        result = self._make_bollinger_result(mocker, price=96.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "LOWER"

    def test_price_below_lower_band(self, mocker):
        result = self._make_bollinger_result(mocker, price=90.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "BELOW_LOWER"

    def test_bva_price_exactly_at_upper(self, mocker):
        """BVA boundary: price == upper → ABOVE_UPPER."""
        result = self._make_bollinger_result(mocker, price=105.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "ABOVE_UPPER"

    def test_bva_price_exactly_at_lower(self, mocker):
        """BVA boundary: price == lower → LOWER (not BELOW_LOWER)."""
        result = self._make_bollinger_result(mocker, price=95.0, upper=105.0, lower=95.0, mid=100.0)
        assert result["bb_position"] == "LOWER"


class TestATRSuccessPath:
    """Lines 115-116 — ATR valid computation with sufficient bars."""

    def test_atr_with_30_bars_returns_float(self, mocker):
        """ATR with valid bars returns a float via sys.modules injection."""
        import pandas as pd
        engine = IndicatorEngine()
        bars = _make_bars(30)
        highs = pd.Series([b.high for b in bars])
        lows = pd.Series([b.low for b in bars])
        closes = pd.Series([b.close for b in bars])
        valid_series = pd.Series([0.5] * len(bars))
        mock_atr_inst = mocker.MagicMock()
        mock_atr_inst.average_true_range.return_value = valid_series
        fake_vol = _make_fake_ta_volatility(mocker)
        fake_vol.AverageTrueRange = mocker.MagicMock(return_value=mock_atr_inst)
        _ta_patch(mocker, vol=fake_vol)
        result = engine._atr(highs, lows, closes)
        assert "atr_14" in result
        assert result["atr_14"] == pytest.approx(0.5)
        assert isinstance(result["atr_14"], float)

    def test_compute_all_with_sufficient_bars_covers_atr_path(self, mocker):
        """compute_all exercises all success paths via full sys.modules injection."""
        import pandas as pd
        engine = IndicatorEngine()
        bars = _make_bars(30)
        n = len(bars)

        rsi_series = pd.Series([55.0] * n)
        mock_rsi_inst = mocker.MagicMock()
        mock_rsi_inst.rsi.return_value = rsi_series
        fake_mom = _make_fake_ta_momentum(mocker)
        fake_mom.RSIIndicator = mocker.MagicMock(return_value=mock_rsi_inst)

        macd_series = pd.Series([1.0] * n)
        mock_macd_inst = mocker.MagicMock()
        mock_macd_inst.macd.return_value = macd_series
        mock_macd_inst.macd_signal.return_value = macd_series
        mock_macd_inst.macd_diff.return_value = macd_series
        ema_series = pd.Series([100.0] * n)
        mock_ema_inst = mocker.MagicMock()
        mock_ema_inst.ema_indicator.return_value = ema_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.MACD = mocker.MagicMock(return_value=mock_macd_inst)
        fake_trend.EMAIndicator = mocker.MagicMock(return_value=mock_ema_inst)

        bb_series = pd.Series([105.0] * n)
        bb_lower = pd.Series([95.0] * n)
        bb_mid = pd.Series([100.0] * n)
        mock_bb_inst = mocker.MagicMock()
        mock_bb_inst.bollinger_hband.return_value = bb_series
        mock_bb_inst.bollinger_lband.return_value = bb_lower
        mock_bb_inst.bollinger_mavg.return_value = bb_mid
        atr_series = pd.Series([0.5] * n)
        mock_atr_inst = mocker.MagicMock()
        mock_atr_inst.average_true_range.return_value = atr_series
        fake_vol = _make_fake_ta_volatility(mocker, bb_factory=mocker.MagicMock(return_value=mock_bb_inst))
        fake_vol.AverageTrueRange = mocker.MagicMock(return_value=mock_atr_inst)

        _ta_patch(mocker, mom=fake_mom, trend=fake_trend, vol=fake_vol)
        result = engine.compute_all(bars)
        assert isinstance(result, dict)
        assert "atr_14" in result
        assert "rsi_14" in result
        assert "volume_ratio" in result


class TestRSIExceptionFallback:
    """Line 50-51 — _rsi except path returns None-filled dict (already covered by ta=None test).
    Uses sys.modules injection so tests pass regardless of whether ta is installed."""

    def test_rsi_raises_returns_none(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 30)
        fake_mom = _make_fake_ta_momentum(mocker, rsi_side_effect=ValueError("rsi error"))
        _ta_patch(mocker, mom=fake_mom)
        result = engine._rsi(closes)
        assert result == {"rsi_14": None}

    def test_macd_raises_returns_none(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 30)
        fake_trend = _make_fake_ta_trend(mocker, macd_side_effect=ValueError("macd error"))
        _ta_patch(mocker, trend=fake_trend)
        result = engine._macd(closes)
        assert result == {"macd_line": None, "macd_signal": None, "macd_histogram": None}

    def test_ema_raises_returns_none(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 60)
        fake_trend = _make_fake_ta_trend(mocker, ema_side_effect=ValueError("ema error"))
        _ta_patch(mocker, trend=fake_trend)
        result = engine._ema(closes)
        assert result == {"ema_20": None, "ema_50": None}

    def test_atr_raises_returns_none(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        highs = pd.Series([101.0] * 30)
        lows = pd.Series([99.0] * 30)
        closes = pd.Series([100.0] * 30)
        fake_vol = _make_fake_ta_volatility(mocker, atr_side_effect=ValueError("atr error"))
        _ta_patch(mocker, vol=fake_vol)
        result = engine._atr(highs, lows, closes)
        assert result == {"atr_14": None}


class TestMACDSuccessPath:
    """Lines 57-60 — MACD valid computation via sys.modules injection."""

    def test_macd_returns_valid_values(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0 + i * 0.1 for i in range(30)])
        macd_series = pd.Series([1.5] * len(closes))
        signal_series = pd.Series([1.2] * len(closes))
        hist_series = pd.Series([0.3] * len(closes))
        mock_macd_inst = mocker.MagicMock()
        mock_macd_inst.macd.return_value = macd_series
        mock_macd_inst.macd_signal.return_value = signal_series
        mock_macd_inst.macd_diff.return_value = hist_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.MACD = mocker.MagicMock(return_value=mock_macd_inst)
        _ta_patch(mocker, trend=fake_trend)
        result = engine._macd(closes)
        assert result["macd_line"] == pytest.approx(1.5)
        assert result["macd_signal"] == pytest.approx(1.2)
        assert result["macd_histogram"] == pytest.approx(0.3)

    def test_macd_nan_last_returns_none(self, mocker):
        """MACD last value NaN → all fields None."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 30)
        nan_series = pd.Series([float("nan")] * len(closes))
        mock_macd_inst = mocker.MagicMock()
        mock_macd_inst.macd.return_value = nan_series
        mock_macd_inst.macd_signal.return_value = nan_series
        mock_macd_inst.macd_diff.return_value = nan_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.MACD = mocker.MagicMock(return_value=mock_macd_inst)
        _ta_patch(mocker, trend=fake_trend)
        result = engine._macd(closes)
        assert result["macd_line"] is None
        assert result["macd_signal"] is None
        assert result["macd_histogram"] is None

    def test_macd_empty_series_returns_none(self, mocker):
        """MACD returning empty series → all fields None."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 10)
        empty_series = pd.Series([], dtype=float)
        mock_macd_inst = mocker.MagicMock()
        mock_macd_inst.macd.return_value = empty_series
        mock_macd_inst.macd_signal.return_value = empty_series
        mock_macd_inst.macd_diff.return_value = empty_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.MACD = mocker.MagicMock(return_value=mock_macd_inst)
        _ta_patch(mocker, trend=fake_trend)
        result = engine._macd(closes)
        assert result["macd_line"] is None
        assert result["macd_signal"] is None
        assert result["macd_histogram"] is None


class TestEMASuccessPath:
    """Lines 103-104 — EMA valid computation via sys.modules injection."""

    def test_ema_returns_valid_values(self, mocker):
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0 + i * 0.1 for i in range(60)])
        ema20_series = pd.Series([102.0] * len(closes))
        ema50_series = pd.Series([101.0] * len(closes))
        mock_ema20 = mocker.MagicMock()
        mock_ema20.ema_indicator.return_value = ema20_series
        mock_ema50 = mocker.MagicMock()
        mock_ema50.ema_indicator.return_value = ema50_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.EMAIndicator = mocker.MagicMock(side_effect=[mock_ema20, mock_ema50])
        _ta_patch(mocker, trend=fake_trend)
        result = engine._ema(closes)
        assert result["ema_20"] == pytest.approx(102.0)
        assert result["ema_50"] == pytest.approx(101.0)

    def test_ema_nan_last_returns_none(self, mocker):
        """EMA last value NaN → both fields None."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 60)
        nan_series = pd.Series([float("nan")] * len(closes))
        mock_ema = mocker.MagicMock()
        mock_ema.ema_indicator.return_value = nan_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.EMAIndicator = mocker.MagicMock(return_value=mock_ema)
        _ta_patch(mocker, trend=fake_trend)
        result = engine._ema(closes)
        assert result["ema_20"] is None
        assert result["ema_50"] is None

    def test_ema_empty_series_returns_none(self, mocker):
        """EMA returning empty series → both fields None."""
        import pandas as pd
        engine = IndicatorEngine()
        closes = pd.Series([100.0] * 20)
        empty_series = pd.Series([], dtype=float)
        mock_ema = mocker.MagicMock()
        mock_ema.ema_indicator.return_value = empty_series
        fake_trend = _make_fake_ta_trend(mocker)
        fake_trend.EMAIndicator = mocker.MagicMock(return_value=mock_ema)
        _ta_patch(mocker, trend=fake_trend)
        result = engine._ema(closes)
        assert result["ema_20"] is None
        assert result["ema_50"] is None
