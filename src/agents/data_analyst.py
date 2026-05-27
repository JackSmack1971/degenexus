"""Data Analyst Agent: market data + indicators → structured signal."""

from __future__ import annotations
import logging
from typing import Optional

from .base_agent import BaseAgent
from ..models.signals import MarketSignal, IndicatorSnapshot, EntryZone, Trend, SignalStrength, DataQuality
from ..models.trade import Direction
from ..data.market_feed import MarketFeed, OHLCVBar
from ..data.indicators import IndicatorEngine

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Data Analyst at an AI trading firm.
Your job: analyze OHLCV data and technical indicators to generate a precise, evidence-backed market signal.

Rules:
- Base ALL conclusions on the data provided. Never invent data.
- Express confidence as a decimal between 0.0 and 1.0.
- If indicators conflict, reduce confidence — do not pick sides.
- direction must be exactly "LONG" or "SHORT".
- trend must be one of: BULLISH, BEARISH, NEUTRAL, VOLATILE.
- signal_strength must be one of: WEAK, MODERATE, STRONG.
- reasoning must cite specific indicator values, not vague descriptions.
- invalidation_level: the price at which your analysis is definitively wrong.

Respond ONLY with JSON. No commentary outside the JSON object."""


class DataAnalystAgent(BaseAgent):

    def __init__(self, performance_context: str = "") -> None:
        super().__init__("DATA_ANALYST", performance_context)
        self.feed = MarketFeed(alpha_vantage_key=None)
        self.engine = IndicatorEngine()

    def analyze(self, symbol: str) -> Optional[MarketSignal]:
        """Fetch data, compute indicators, generate signal. Returns None on data failure."""
        try:
            bars = self.feed.fetch(symbol, period="90d", interval="1d")
            if len(bars) < 30:
                logger.warning("Insufficient bars for %s (%d)", symbol, len(bars))
                return None

            current_price = bars[-1].close
            data_quality = DataQuality.SYNTHETIC if any(b.source == "SYNTHETIC" for b in bars) \
                else (DataQuality.STALE if any(b.is_stale for b in bars) else DataQuality.LIVE)

            indicators = self.engine.compute_all(bars)
            bar_summary = self._build_bar_summary(bars[-20:], indicators)

            response = self.call_llm(
                system_prompt=SYSTEM_PROMPT,
                user_message=bar_summary,
            )

            return self._parse_signal(response, symbol, current_price, indicators, data_quality)

        except Exception as exc:
            logger.error("DataAnalyst failed for %s: %s", symbol, exc)
            return None

    def _build_bar_summary(self, bars: list[OHLCVBar], indicators: dict) -> str:
        price_history = "\n".join(
            f"  {b.timestamp.date()} O:{b.open:.2f} H:{b.high:.2f} L:{b.low:.2f} C:{b.close:.2f} V:{b.volume:,.0f}"
            for b in bars[-10:]
        )
        ind_lines = "\n".join(
            f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}"
            for k, v in indicators.items()
            if v is not None
        )

        return f"""Analyze this equity data and generate a trading signal.

SYMBOL: {bars[-1].symbol if bars else 'UNKNOWN'}
CURRENT PRICE: {bars[-1].close:.4f}

RECENT PRICE HISTORY (last 10 bars):
{price_history}

COMPUTED INDICATORS:
{ind_lines}

Generate a complete MarketSignal JSON for this symbol. Include:
- direction (LONG or SHORT)
- trend (BULLISH/BEARISH/NEUTRAL/VOLATILE)
- confidence (0.0-1.0)
- signal_strength (WEAK/MODERATE/STRONG)
- entry_zone with low and high prices
- invalidation_level
- detailed reasoning citing specific indicator values
- market_context if observable from the data"""

    def _parse_signal(
        self,
        response: dict,
        symbol: str,
        current_price: float,
        raw_indicators: dict,
        data_quality: DataQuality,
    ) -> Optional[MarketSignal]:
        try:
            ind_data = {k: v for k, v in raw_indicators.items()
                        if k in IndicatorSnapshot.model_fields}
            indicators = IndicatorSnapshot(**ind_data)

            entry_zone_data = response.get("entry_zone", {})
            if isinstance(entry_zone_data, dict):
                entry_zone = EntryZone(
                    low=float(entry_zone_data.get("low", current_price * 0.995)),
                    high=float(entry_zone_data.get("high", current_price * 1.005)),
                )
            else:
                entry_zone = EntryZone(low=current_price * 0.995, high=current_price * 1.005)

            return MarketSignal(
                symbol=symbol,
                direction=Direction(str(response.get("direction", "LONG")).upper()),
                trend=Trend(str(response.get("trend", "NEUTRAL")).upper()),
                entry_zone=entry_zone,
                indicators=indicators,
                confidence=max(0.0, min(1.0, float(response.get("confidence", 0.5)))),
                signal_strength=SignalStrength(
                    str(response.get("signal_strength", "WEAK")).upper()
                ),
                reasoning=str(response.get("reasoning", "Indicator-based analysis")),
                invalidation_level=float(
                    response.get("invalidation_level", current_price * 0.95)
                ),
                data_quality=data_quality,
                market_context=str(response.get("market_context", "")),
                current_price=current_price,
            )
        except Exception as exc:
            logger.error("Failed to parse signal response for %s: %s — response: %s", symbol, exc, response)
            return None

    def _fallback(self, context: str) -> dict:
        return {
            "direction": "LONG",
            "trend": "NEUTRAL",
            "confidence": 0.45,
            "signal_strength": "WEAK",
            "entry_zone": {"low": 0, "high": 0},
            "invalidation_level": 0,
            "reasoning": "[FALLBACK] LLM unavailable — below minimum confidence threshold",
            "market_context": "LLM unavailable",
        }
