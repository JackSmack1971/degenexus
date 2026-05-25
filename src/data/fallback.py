"""Synthetic OHLCV generator — used when all real data sources fail."""

from __future__ import annotations
import random
import math
from datetime import datetime, timezone, timedelta
from .market_feed import OHLCVBar


class SyntheticDataGenerator:
    """
    Generates plausible but clearly synthetic OHLCV data.
    Uses geometric Brownian motion to produce realistic-looking price series.
    All synthetic bars are flagged with source='SYNTHETIC'.
    """

    # Rough starting prices by well-known symbols
    PRICE_MAP: dict[str, float] = {
        "AAPL": 175.0,
        "SPY": 520.0,
        "QQQ": 430.0,
        "NVDA": 850.0,
        "TSLA": 175.0,
        "MSFT": 410.0,
        "AMZN": 185.0,
        "GOOGL": 175.0,
        "META": 500.0,
    }
    DEFAULT_PRICE = 100.0
    DAILY_VOL = 0.015
    DAILY_DRIFT = 0.0001

    def __init__(self, seed: int | None = None) -> None:
        if seed is not None:
            random.seed(seed)

    def generate(self, symbol: str, n_bars: int = 60) -> list[OHLCVBar]:
        start_price = self.PRICE_MAP.get(symbol.upper(), self.DEFAULT_PRICE)
        price = start_price
        bars = []
        now = datetime.now(timezone.utc)

        for i in range(n_bars):
            dt = now - timedelta(days=n_bars - i)
            daily_return = random.gauss(self.DAILY_DRIFT, self.DAILY_VOL)
            close = price * math.exp(daily_return)

            intraday_range = close * random.uniform(0.005, 0.025)
            high = close + random.uniform(0, intraday_range)
            low = close - random.uniform(0, intraday_range)
            open_price = low + random.uniform(0, high - low)

            bar = OHLCVBar(
                symbol=symbol,
                timestamp=dt,
                open=round(open_price, 4),
                high=round(high, 4),
                low=round(low, 4),
                close=round(close, 4),
                volume=float(random.randint(1_000_000, 50_000_000)),
                source="SYNTHETIC",
                is_stale=False,
            )
            bars.append(bar)
            price = close

        return bars
