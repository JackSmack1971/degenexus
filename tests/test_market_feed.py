"""Tests for MarketFeed fallback chain, cache mutation, and price fetching."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from src.data.market_feed import MarketFeed, DataCache, OHLCVBar


def _make_bar(symbol: str = "AAPL", close: float = 150.0, is_stale: bool = False) -> OHLCVBar:
    return OHLCVBar(
        symbol=symbol,
        timestamp=datetime.now(timezone.utc),
        open=close - 1.0,
        high=close + 1.0,
        low=close - 2.0,
        close=close,
        volume=1_000_000.0,
        source="yfinance",
        is_stale=is_stale,
    )


def _make_cache(bars: list[OHLCVBar], age_seconds: float = 0.0) -> DataCache:
    fetched_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    return DataCache(bars=bars, fetched_at=fetched_at)


class TestFallbackChain:
    def test_yfinance_success_returns_bars(self):
        feed = MarketFeed()
        bars = [_make_bar()]
        feed._fetch_yfinance = MagicMock(return_value=bars)
        result = feed.fetch("AAPL")
        assert result == bars

    def test_yfinance_fail_uses_fresh_cache(self):
        feed = MarketFeed()
        cached_bars = [_make_bar(close=140.0)]
        feed._cache["AAPL"] = _make_cache(cached_bars, age_seconds=100.0)
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("network error"))

        with patch("time.sleep"):  # avoid actual sleeps
            result = feed.fetch("AAPL")

        assert result == cached_bars

    def test_yfinance_fail_stale_cache_uses_synthetic(self):
        feed = MarketFeed()
        cached_bars = [_make_bar(close=140.0)]
        # Cache older than CACHE_MAX_AGE_SECONDS (7200s)
        feed._cache["AAPL"] = _make_cache(cached_bars, age_seconds=8000.0)
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("network error"))

        with patch("time.sleep"):
            result = feed.fetch("AAPL")

        # Should fall through to synthetic data
        assert len(result) > 0
        assert all(b.source == "SYNTHETIC" for b in result)

    def test_yfinance_fail_no_cache_uses_synthetic(self):
        feed = MarketFeed()
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("network error"))

        with patch("time.sleep"):
            result = feed.fetch("AAPL")

        assert len(result) > 0
        assert all(b.source == "SYNTHETIC" for b in result)

    def test_successful_fetch_populates_cache(self):
        feed = MarketFeed()
        bars = [_make_bar()]
        feed._fetch_yfinance = MagicMock(return_value=bars)
        feed.fetch("AAPL")
        assert "AAPL" in feed._cache
        assert feed._cache["AAPL"].bars == bars


class TestStaleCacheMutation:
    def test_stale_cache_marks_bars_is_stale_true(self):
        feed = MarketFeed()
        bar = _make_bar(is_stale=False)
        feed._cache["AAPL"] = _make_cache([bar], age_seconds=100.0)
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("fail"))

        with patch("time.sleep"):
            result = feed.fetch("AAPL")

        assert all(b.is_stale is True for b in result)

    def test_stale_mutation_is_idempotent(self):
        """Calling fetch twice with stale cache doesn't further corrupt bars."""
        feed = MarketFeed()
        bar = _make_bar(is_stale=False)
        feed._cache["AAPL"] = _make_cache([bar], age_seconds=100.0)
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("fail"))

        with patch("time.sleep"):
            result1 = feed.fetch("AAPL")
            result2 = feed.fetch("AAPL")

        # Both fetches return the same bar with is_stale=True
        assert all(b.is_stale is True for b in result1)
        assert all(b.is_stale is True for b in result2)


class TestGetCurrentPrice:
    def test_returns_last_close_on_success(self):
        feed = MarketFeed()
        bars = [_make_bar(close=151.0), _make_bar(close=152.5)]
        feed._fetch_yfinance = MagicMock(return_value=bars)
        price = feed.get_current_price("AAPL")
        assert price == pytest.approx(152.5)

    def test_returns_none_on_total_failure(self):
        feed = MarketFeed()
        # Make both yfinance and synthetic fail — patch the synthetic generator
        feed._fetch_yfinance = MagicMock(side_effect=RuntimeError("fail"))

        with patch("time.sleep"), \
             patch("src.data.fallback.SyntheticDataGenerator.generate", side_effect=RuntimeError("also fail")):
            price = feed.get_current_price("AAPL")

        assert price is None

    def test_returns_none_when_bars_empty(self):
        feed = MarketFeed()
        # fetch returns empty list despite no exception
        with patch.object(feed, "fetch", return_value=[]):
            price = feed.get_current_price("AAPL")
        assert price is None


class TestDataCacheAge:
    def test_fresh_cache_not_stale(self):
        bars = [_make_bar()]
        cache = _make_cache(bars, age_seconds=0.0)
        assert cache.is_stale(7200.0) is False

    def test_old_cache_is_stale(self):
        bars = [_make_bar()]
        cache = _make_cache(bars, age_seconds=8000.0)
        assert cache.is_stale(7200.0) is True

    def test_cache_age_just_below_boundary_not_stale(self):
        bars = [_make_bar()]
        cache = _make_cache(bars, age_seconds=7199.0)
        assert cache.is_stale(7200.0) is False

    def test_cache_age_just_above_boundary_is_stale(self):
        bars = [_make_bar()]
        cache = _make_cache(bars, age_seconds=7201.0)
        assert cache.is_stale(7200.0) is True
