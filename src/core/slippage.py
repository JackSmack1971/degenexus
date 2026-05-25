"""Slippage simulation: bid-ask spread + market impact + gaussian noise."""

from __future__ import annotations
import random
import math


class SlippageModel:
    """
    Three-component slippage model:
    1. Spread component (0.05% baseline for liquid US equities)
    2. Market impact (linear in order size — negligible at retail scale)
    3. Microstructure noise (gaussian, zero-mean)
    """

    def __init__(
        self,
        base_spread_pct: float = 0.0005,
        impact_per_million: float = 0.0001,
        noise_std: float = 0.0002,
        seed: int | None = None,
    ) -> None:
        self.base_spread_pct = base_spread_pct
        self.impact_per_million = impact_per_million
        self.noise_std = noise_std
        if seed is not None:
            random.seed(seed)

    def compute(
        self,
        order_value_usd: float,
        direction: str,
    ) -> tuple[float, float]:
        """
        Returns (slippage_pct, slippage_usd).
        Positive slippage_pct = you paid more (LONG buy) or received less (SHORT sell).
        """
        spread = self.base_spread_pct
        impact = order_value_usd * self.impact_per_million / 1_000_000
        noise = abs(random.gauss(0, self.noise_std))

        total_pct = spread + impact + noise

        slippage_usd = order_value_usd * total_pct
        return total_pct, slippage_usd

    def apply_to_price(
        self,
        price: float,
        direction: str,
        order_value_usd: float,
    ) -> tuple[float, float]:
        """
        Returns (fill_price, slippage_pct).
        For LONG: fill_price > requested (you buy higher).
        For SHORT: fill_price < requested (you sell lower).
        """
        slippage_pct, _ = self.compute(order_value_usd, direction)

        if direction == "LONG":
            fill_price = price * (1 + slippage_pct)
        else:
            fill_price = price * (1 - slippage_pct)

        return round(fill_price, 4), slippage_pct


def select_order_type(signal_confidence: float, price_distance_pct: float) -> str:
    """
    Market order: high confidence + price is near current level.
    Limit order: everything else — never chase.
    """
    if signal_confidence >= 0.85 and price_distance_pct < 0.002:
        return "MARKET"
    return "LIMIT"
