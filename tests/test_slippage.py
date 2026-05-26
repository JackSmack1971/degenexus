"""Tests for SlippageModel and order type selection."""

import pytest
from src.core.slippage import SlippageModel, select_order_type


class TestSlippageModel:
    def test_long_buy_price_is_higher(self):
        model = SlippageModel(seed=42)
        fill, slip_pct = model.apply_to_price(100.0, "LONG", 1000.0)
        assert fill > 100.0
        assert slip_pct > 0

    def test_short_sell_price_is_lower(self):
        model = SlippageModel(seed=42)
        fill, slip_pct = model.apply_to_price(100.0, "SHORT", 1000.0)
        assert fill < 100.0
        assert slip_pct > 0

    def test_slippage_pct_is_positive(self):
        model = SlippageModel(seed=42)
        _, slip = model.apply_to_price(150.0, "LONG", 1500.0)
        assert 0 < slip < 0.01

    def test_larger_order_has_higher_impact(self):
        model = SlippageModel(seed=42)
        _, slip_small = model.compute(1_000.0)
        model2 = SlippageModel(seed=42)
        _, slip_large = model2.compute(1_000_000.0)
        assert slip_large > slip_small

    def test_zero_price_does_not_crash(self):
        model = SlippageModel(seed=42)
        fill, _ = model.apply_to_price(0.0, "LONG", 0.0)
        assert fill == 0.0

    def test_slippage_components_are_reasonable(self):
        model = SlippageModel(
            base_spread_pct=0.001,
            impact_per_million=0.0001,
            noise_std=0.0001,
            seed=99,
        )
        total_pct, _ = model.compute(10_000.0)
        assert 0.0005 < total_pct < 0.005

    def test_fill_price_rounded_to_4dp(self):
        model = SlippageModel(seed=0)
        fill, _ = model.apply_to_price(150.123456789, "LONG", 1500.0)
        assert fill == round(fill, 4)


class TestOrderTypeSelection:
    def test_high_confidence_near_price_is_market(self):
        result = select_order_type(signal_confidence=0.90, price_distance_pct=0.001)
        assert result == "MARKET"

    def test_moderate_confidence_is_limit(self):
        result = select_order_type(signal_confidence=0.70, price_distance_pct=0.005)
        assert result == "LIMIT"

    def test_low_confidence_always_limit(self):
        result = select_order_type(signal_confidence=0.50, price_distance_pct=0.001)
        assert result == "LIMIT"

    def test_high_confidence_far_from_price_is_limit(self):
        result = select_order_type(signal_confidence=0.95, price_distance_pct=0.01)
        assert result == "LIMIT"

    def test_boundary_85pct_confidence_near_is_market(self):
        result = select_order_type(signal_confidence=0.85, price_distance_pct=0.001)
        assert result == "MARKET"

    def test_boundary_84pct_confidence_is_limit(self):
        result = select_order_type(signal_confidence=0.84, price_distance_pct=0.001)
        assert result == "LIMIT"
