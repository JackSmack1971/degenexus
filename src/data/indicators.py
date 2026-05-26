"""Technical indicator computation using the `ta` library."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


class IndicatorEngine:
    """
    Computes RSI, MACD, Bollinger Bands, EMA, ATR, and volume ratios.
    Uses the `ta` library (pure pandas/numpy, no numba dependency).
    Returns structured dicts safe to plug into IndicatorSnapshot.
    Fails gracefully — missing indicators return None, not exceptions.
    """

    def compute_all(self, bars: list) -> dict:
        """
        bars: list of OHLCVBar
        Returns dict matching IndicatorSnapshot field names.
        """
        try:
            import pandas as pd

            closes = pd.Series([b.close for b in bars])
            highs = pd.Series([b.high for b in bars])
            lows = pd.Series([b.low for b in bars])
            volumes = pd.Series([b.volume for b in bars])

            result: dict = {}
            result.update(self._rsi(closes))
            result.update(self._macd(closes))
            result.update(self._bollinger(closes))
            result.update(self._ema(closes))
            result.update(self._atr(highs, lows, closes))
            result.update(self._volume_ratio(volumes))

            return result

        except Exception as exc:
            logger.error("Indicator computation failed: %s", exc)
            return {}

    def _rsi(self, closes) -> dict:
        try:
            import ta.momentum as mom
            rsi = mom.RSIIndicator(close=closes, window=14).rsi()
            val = float(rsi.iloc[-1]) if not rsi.empty and not rsi.isna().iloc[-1] else None
            return {"rsi_14": val}
        except Exception:
            return {"rsi_14": None}

    def _macd(self, closes) -> dict:
        try:
            import ta.trend as trend
            macd_ind = trend.MACD(close=closes, window_slow=26, window_fast=12, window_sign=9)
            macd_line = macd_ind.macd()
            macd_signal = macd_ind.macd_signal()
            macd_hist = macd_ind.macd_diff()
            return {
                "macd_line": float(macd_line.iloc[-1]) if not macd_line.empty and not macd_line.isna().iloc[-1] else None,
                "macd_signal": float(macd_signal.iloc[-1]) if not macd_signal.empty and not macd_signal.isna().iloc[-1] else None,
                "macd_histogram": float(macd_hist.iloc[-1]) if not macd_hist.empty and not macd_hist.isna().iloc[-1] else None,
            }
        except Exception:
            return {"macd_line": None, "macd_signal": None, "macd_histogram": None}

    def _bollinger(self, closes) -> dict:
        try:
            import math
            import ta.volatility as vol
            bb = vol.BollingerBands(close=closes, window=20, window_dev=2)
            upper = bb.bollinger_hband().iloc[-1]
            lower = bb.bollinger_lband().iloc[-1]
            mid = bb.bollinger_mavg().iloc[-1]
            if math.isnan(upper) or math.isnan(lower) or math.isnan(mid):
                return {"bb_upper": None, "bb_lower": None, "bb_position": None}
            price = float(closes.iloc[-1])

            if price >= upper:
                pos = "ABOVE_UPPER"
            elif price >= mid + (upper - mid) * 0.5:
                pos = "UPPER"
            elif price >= mid - (mid - lower) * 0.5:
                pos = "MID"
            elif price >= lower:
                pos = "LOWER"
            else:
                pos = "BELOW_LOWER"

            return {
                "bb_upper": float(upper),
                "bb_lower": float(lower),
                "bb_position": pos,
            }
        except Exception:
            return {"bb_upper": None, "bb_lower": None, "bb_position": None}

    def _ema(self, closes) -> dict:
        try:
            import ta.trend as trend
            ema20 = trend.EMAIndicator(close=closes, window=20).ema_indicator()
            ema50 = trend.EMAIndicator(close=closes, window=50).ema_indicator()
            return {
                "ema_20": float(ema20.iloc[-1]) if not ema20.empty and not ema20.isna().iloc[-1] else None,
                "ema_50": float(ema50.iloc[-1]) if not ema50.empty and not ema50.isna().iloc[-1] else None,
            }
        except Exception:
            return {"ema_20": None, "ema_50": None}

    def _atr(self, highs, lows, closes) -> dict:
        try:
            import ta.volatility as vol
            atr = vol.AverageTrueRange(high=highs, low=lows, close=closes, window=14).average_true_range()
            val = float(atr.iloc[-1]) if not atr.empty and not atr.isna().iloc[-1] else None
            return {"atr_14": val}
        except Exception:
            return {"atr_14": None}

    def _volume_ratio(self, volumes) -> dict:
        try:
            recent_vol = float(volumes.iloc[-1])
            avg_vol = float(volumes.tail(20).mean())
            ratio = recent_vol / avg_vol if avg_vol > 0 else 1.0
            return {"volume_ratio": round(ratio, 2)}
        except Exception:
            return {"volume_ratio": None}
