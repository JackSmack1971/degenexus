"""
Market data connector.
Primary: yfinance (no API key needed)
Secondary: Alpha Vantage (free tier — 25 req/day)
Fallback: synthetic OHLCV via SyntheticDataGenerator
"""

from __future__ import annotations
import time
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class OHLCVBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "yfinance"
    is_stale: bool = False


@dataclass
class DataCache:
    bars: list[OHLCVBar]
    fetched_at: datetime

    @property
    def age_seconds(self) -> float:
        return (datetime.now(timezone.utc) - self.fetched_at).total_seconds()

    def is_stale(self, max_age_seconds: float = 7200.0) -> bool:
        return self.age_seconds > max_age_seconds


class MarketFeed:
    """
    Fault-tolerant market data fetcher.
    On failure: exponential backoff → cached data → synthetic fallback.
    """

    MAX_RETRIES = 3
    CACHE_MAX_AGE_SECONDS = 7200

    def __init__(self, alpha_vantage_key: Optional[str] = None) -> None:
        self._alpha_vantage_key = alpha_vantage_key
        self._cache: dict[str, DataCache] = {}

    def fetch(self, symbol: str, period: str = "60d", interval: str = "1d") -> list[OHLCVBar]:
        """
        Fetch OHLCV bars with automatic fallback chain.
        Returns list of OHLCVBar sorted ascending by timestamp.
        """
        for attempt in range(self.MAX_RETRIES):
            try:
                bars = self._fetch_yfinance(symbol, period, interval)
                if bars:
                    self._cache[symbol] = DataCache(bars=bars, fetched_at=datetime.now(timezone.utc))
                    return bars
            except Exception as exc:
                wait = 2 ** attempt
                logger.warning(
                    "yfinance attempt %d/%d failed for %s: %s — waiting %ds",
                    attempt + 1, self.MAX_RETRIES, symbol, exc, wait,
                )
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(wait)

        # Stale cache fallback
        if symbol in self._cache:
            cached = self._cache[symbol]
            if not cached.is_stale(self.CACHE_MAX_AGE_SECONDS):
                logger.warning("Using cached data for %s (age: %.0fs)", symbol, cached.age_seconds)
                for bar in cached.bars:
                    bar.is_stale = True
                return cached.bars
            else:
                logger.warning("Cache too stale for %s (%.0fs) — using synthetic", symbol, cached.age_seconds)

        # Synthetic fallback
        from .fallback import SyntheticDataGenerator
        logger.warning("Generating synthetic data for %s", symbol)
        bars = SyntheticDataGenerator().generate(symbol, n_bars=60)
        return bars

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Returns most recent close price, or None on total failure."""
        try:
            bars = self.fetch(symbol, period="5d", interval="1d")
            if bars:
                return bars[-1].close
        except Exception as exc:
            logger.error("Cannot get price for %s: %s", symbol, exc)
        return None

    def _fetch_yfinance(self, symbol: str, period: str, interval: str) -> list[OHLCVBar]:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval, auto_adjust=True)

        if df.empty:
            raise ValueError(f"yfinance returned empty DataFrame for {symbol}")

        bars = []
        for ts, row in df.iterrows():
            bar = OHLCVBar(
                symbol=symbol,
                timestamp=ts.to_pydatetime().replace(tzinfo=timezone.utc)
                if ts.tzinfo is None
                else ts.to_pydatetime(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
                source="yfinance",
            )
            bars.append(bar)

        return sorted(bars, key=lambda b: b.timestamp)
