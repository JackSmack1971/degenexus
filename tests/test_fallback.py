"""Tests for SyntheticDataGenerator OHLCV integrity."""

from src.data.fallback import SyntheticDataGenerator


class TestSyntheticBarCount:
    def test_default_generates_60_bars(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL")
        assert len(bars) == 60

    def test_custom_n_bars(self):
        gen = SyntheticDataGenerator(seed=1)
        bars = gen.generate("AAPL", n_bars=30)
        assert len(bars) == 30

    def test_zero_bars(self):
        gen = SyntheticDataGenerator(seed=0)
        bars = gen.generate("AAPL", n_bars=0)
        assert bars == []


class TestSyntheticBarSource:
    def test_all_bars_have_source_synthetic(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("TSLA")
        assert all(b.source == "SYNTHETIC" for b in bars)

    def test_is_stale_false_on_all_bars(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL")
        assert all(b.is_stale is False for b in bars)

    def test_symbol_set_on_all_bars(self):
        gen = SyntheticDataGenerator(seed=7)
        bars = gen.generate("NVDA")
        assert all(b.symbol == "NVDA" for b in bars)


class TestSyntheticOHLCInvariants:
    def test_high_gte_close_gte_low(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL", n_bars=60)
        for bar in bars:
            assert bar.high >= bar.close, f"high={bar.high} < close={bar.close}"
            assert bar.close >= bar.low, f"close={bar.close} < low={bar.low}"

    def test_all_prices_positive(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL", n_bars=60)
        for bar in bars:
            assert bar.open > 0
            assert bar.high > 0
            assert bar.low > 0
            assert bar.close > 0

    def test_volume_positive(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL", n_bars=60)
        assert all(b.volume > 0 for b in bars)

    def test_high_gte_open_and_low_lte_open(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("SPY", n_bars=60)
        for bar in bars:
            assert bar.high >= bar.open, f"high={bar.high} < open={bar.open}"
            assert bar.low <= bar.open, f"low={bar.low} > open={bar.open}"


class TestSyntheticTimestamps:
    def test_timestamps_strictly_ascending(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL", n_bars=30)
        timestamps = [b.timestamp for b in bars]
        for i in range(1, len(timestamps)):
            assert timestamps[i] > timestamps[i - 1], (
                f"Timestamp not ascending at bar {i}: {timestamps[i-1]} >= {timestamps[i]}"
            )


class TestSyntheticPriceMap:
    def test_known_symbol_uses_price_map(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("AAPL", n_bars=1)
        # Starts at ~175 and can vary, but should be in a broad reasonable range
        assert 50.0 < bars[0].close < 500.0

    def test_unknown_symbol_uses_default_price(self):
        gen = SyntheticDataGenerator(seed=42)
        bars = gen.generate("UNKNOWN_XYZ", n_bars=1)
        # DEFAULT_PRICE = 100.0, should be in reasonable range
        assert 20.0 < bars[0].close < 500.0

    def test_seed_produces_deterministic_output(self):
        bars_a = SyntheticDataGenerator(seed=999).generate("AAPL")
        bars_b = SyntheticDataGenerator(seed=999).generate("AAPL")
        closes_a = [b.close for b in bars_a]
        closes_b = [b.close for b in bars_b]
        assert closes_a == closes_b
