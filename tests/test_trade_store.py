"""Tests for TradeStore persistence."""

import sqlite3
from types import SimpleNamespace

import pytest

from src.memory.trade_store import TradeStore
from src.models.trade import Direction, OrderType, Trade, TradeState


def _make_trade(symbol: str = "AAPL", state: TradeState = TradeState.CLOSED) -> Trade:
    return Trade(
        proposal_id="proposal-1",
        signal_id="signal-1",
        symbol=symbol,
        direction=Direction.LONG,
        state=state,
        order_type=OrderType.LIMIT,
        entry_price=150.0,
        fill_price=150.0,
        shares=5,
        gross_value=750.0,
        stop_loss=147.5,
        take_profit=155.0,
        max_loss_usd=12.5,
        risk_reward_ratio=2.0,
        partial_pnl=5.0,
        realized_pnl=15.0,
    )


def _make_challenge(
    challenge_id: str = "chal-1",
    challenger: str = "CEO",
    challenged_agent: str = "RISK",
    disputed_field: str = "risk_score",
    evidence: dict | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        challenge_id=challenge_id,
        challenger=challenger,
        challenged_agent=challenged_agent,
        disputed_field=disputed_field,
        evidence=evidence or {"reason": "low risk"},
    )


def test_upsert_trade_persists_partial_pnl(tmp_path):
    store = TradeStore(db_path=str(tmp_path / "trades.db"))
    trade = _make_trade()

    store.upsert_trade(trade)
    closed = store.get_closed_trades(limit=1)

    assert closed[0]["partial_pnl"] == 5.0
    assert closed[0]["realized_pnl"] == 15.0


# ---------------------------------------------------------------------------
# Lines 106 — schema migration adds partial_pnl when column is absent
# ---------------------------------------------------------------------------

class TestSchemaMigration:
    def test_migration_adds_partial_pnl_to_legacy_db(self, tmp_path):
        db_path = str(tmp_path / "legacy.db")
        # Create a pre-migration DB: full trades schema but WITHOUT partial_pnl
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                CREATE TABLE trades (
                    trade_id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    state TEXT NOT NULL,
                    order_type TEXT,
                    entry_price REAL,
                    fill_price REAL,
                    slippage_pct REAL,
                    shares INTEGER,
                    stop_loss REAL,
                    take_profit REAL,
                    max_loss_usd REAL,
                    risk_reward_ratio REAL,
                    close_price REAL,
                    close_reason TEXT,
                    realized_pnl REAL,
                    realized_pnl_pct REAL,
                    risk_score REAL,
                    agent_reasoning TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
        # TradeStore._init_db() should detect missing partial_pnl and ALTER TABLE
        TradeStore(db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(trades)").fetchall()}
        assert "partial_pnl" in columns

    def test_fresh_db_has_partial_pnl_from_create(self, tmp_path):
        """Confirm that fresh DBs include partial_pnl (no migration needed)."""
        TradeStore(db_path=str(tmp_path / "fresh.db"))
        with sqlite3.connect(str(tmp_path / "fresh.db")) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(trades)").fetchall()}
        assert "partial_pnl" in columns


# ---------------------------------------------------------------------------
# Lines 167-171 — get_partially_closed_trade_ids
# ---------------------------------------------------------------------------

class TestGetPartiallyClosedTradeIds:
    def test_returns_ids_of_partially_closed_trades(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        t1 = _make_trade(state=TradeState.PARTIALLY_CLOSED)
        t2 = _make_trade(state=TradeState.PARTIALLY_CLOSED)
        t2.trade_id = "different-id"
        t2.proposal_id = "proposal-2"
        t3 = _make_trade(state=TradeState.OPEN)
        t3.trade_id = "open-id"
        t3.proposal_id = "proposal-3"
        store.upsert_trade(t1)
        store.upsert_trade(t2)
        store.upsert_trade(t3)
        ids = store.get_partially_closed_trade_ids()
        assert t1.trade_id in ids
        assert "different-id" in ids
        assert "open-id" not in ids

    def test_returns_empty_list_when_no_partial_trades(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.upsert_trade(_make_trade(state=TradeState.CLOSED))
        assert store.get_partially_closed_trade_ids() == []


# ---------------------------------------------------------------------------
# Lines 182-188 — get_recent_trades
# ---------------------------------------------------------------------------

class TestGetRecentTrades:
    def test_returns_closed_trades_most_recent_first(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.upsert_trade(_make_trade(state=TradeState.CLOSED))
        results = store.get_recent_trades(n=10)
        assert len(results) == 1
        assert results[0]["symbol"] == "AAPL"

    def test_excludes_open_trades(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.upsert_trade(_make_trade(state=TradeState.OPEN))
        results = store.get_recent_trades(n=10)
        assert results == []

    def test_bva_limit_zero(self, tmp_path):
        """BVA: limit=0 returns empty list."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.upsert_trade(_make_trade(state=TradeState.CLOSED))
        assert store.get_recent_trades(n=0) == []


# ---------------------------------------------------------------------------
# Lines 191-197 — get_trades_by_symbol
# ---------------------------------------------------------------------------

class TestGetTradesBySymbol:
    def test_returns_only_closed_trades_for_symbol(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        aapl1 = _make_trade(symbol="AAPL", state=TradeState.CLOSED)
        aapl2 = _make_trade(symbol="AAPL", state=TradeState.CLOSED)
        aapl2.trade_id = "aapl-2"
        aapl2.proposal_id = "proposal-2"
        open_aapl = _make_trade(symbol="AAPL", state=TradeState.OPEN)
        open_aapl.trade_id = "aapl-open"
        open_aapl.proposal_id = "proposal-3"
        tsla = _make_trade(symbol="TSLA", state=TradeState.CLOSED)
        tsla.trade_id = "tsla-1"
        tsla.proposal_id = "proposal-4"
        for t in [aapl1, aapl2, open_aapl, tsla]:
            store.upsert_trade(t)

        results = store.get_trades_by_symbol("AAPL")
        assert len(results) == 2
        assert all(r["symbol"] == "AAPL" for r in results)
        assert all(r["state"] == "CLOSED" for r in results)

    def test_returns_empty_list_for_unknown_symbol(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.upsert_trade(_make_trade(symbol="AAPL"))
        assert store.get_trades_by_symbol("TSLA") == []

    def test_bva_limit_exactly_matches_count(self, tmp_path):
        """BVA: limit == count of matching trades → all returned."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        t1 = _make_trade(symbol="AAPL")
        t2 = _make_trade(symbol="AAPL")
        t2.trade_id = "aapl-2"
        t2.proposal_id = "proposal-2"
        for t in [t1, t2]:
            store.upsert_trade(t)
        assert len(store.get_trades_by_symbol("AAPL", limit=2)) == 2

    def test_bva_limit_less_than_count(self, tmp_path):
        """BVA: limit < count → capped at limit."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        t1 = _make_trade(symbol="AAPL")
        t2 = _make_trade(symbol="AAPL")
        t2.trade_id = "aapl-2"
        t2.proposal_id = "proposal-2"
        for t in [t1, t2]:
            store.upsert_trade(t)
        assert len(store.get_trades_by_symbol("AAPL", limit=1)) == 1


# ---------------------------------------------------------------------------
# Lines 205-206 — log_agent_message
# ---------------------------------------------------------------------------

class TestLogAgentMessage:
    def test_inserts_row_into_agent_decisions(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_agent_message(
            session_id="sess-1",
            cycle_id="cycle-1",
            agent_id="CEO",
            message_type="ANALYSIS",
            payload={"content": "buy signal"},
        )
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            rows = conn.execute("SELECT * FROM agent_decisions").fetchall()
        assert len(rows) == 1
        assert rows[0][3] == "CEO"  # agent_id column

    def test_payload_serialized_as_json(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        payload = {"nested": {"key": [1, 2, 3]}}
        store.log_agent_message("s", "c", "QUANT", "PROPOSAL", payload)
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            import json
            row = conn.execute("SELECT payload FROM agent_decisions").fetchone()
        assert json.loads(row[0]) == payload


# ---------------------------------------------------------------------------
# Lines 216-217 — log_challenge
# ---------------------------------------------------------------------------

class TestLogChallenge:
    def test_log_challenge_inserts_row(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        challenge = _make_challenge()
        store.log_challenge(challenge, accepted=True)
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            rows = conn.execute("SELECT * FROM challenge_log").fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "chal-1"  # challenge_id

    def test_log_challenge_accepted_none(self, tmp_path):
        """accepted=None stores NULL in DB."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge(challenge_id="chal-2"), accepted=None)
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            row = conn.execute("SELECT accepted FROM challenge_log").fetchone()
        assert row[0] is None


# ---------------------------------------------------------------------------
# Lines 241-242 — log_counter_challenge
# ---------------------------------------------------------------------------

class TestLogCounterChallenge:
    def test_inserts_counter_challenge_row(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_counter_challenge(
            challenge_id="counter-1",
            proposal_id="prop-1",
            challenger="CEO",
            challenged_agent="RISK",
            reasoning="low risk profile",
        )
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            rows = conn.execute("SELECT * FROM challenge_log").fetchall()
        assert len(rows) == 1
        assert rows[0][1] == "counter-1"


# ---------------------------------------------------------------------------
# Lines 259-260 — resolve_challenge
# ---------------------------------------------------------------------------

class TestResolveChallenge:
    def test_resolve_challenge_updates_accepted(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge(challenge_id="res-1"), accepted=None)
        store.resolve_challenge("res-1", accepted=True)
        with sqlite3.connect(str(tmp_path / "trades.db")) as conn:
            row = conn.execute("SELECT accepted FROM challenge_log WHERE challenge_id='res-1'").fetchone()
        assert row[0] == 1  # True stored as 1


# ---------------------------------------------------------------------------
# Lines 267-272 — get_challenges
# ---------------------------------------------------------------------------

class TestGetChallenges:
    def test_returns_challenges_most_recent_first(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        for i in range(3):
            store.log_challenge(_make_challenge(challenge_id=f"chal-{i}"))
        results = store.get_challenges(limit=10)
        assert len(results) == 3
        # Sorted DESC by timestamp — most recent id is the last inserted
        timestamps = [r["timestamp"] for r in results]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_bva_limit_zero(self, tmp_path):
        """BVA: limit=0 → empty list."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge())
        assert store.get_challenges(limit=0) == []

    def test_bva_limit_exact(self, tmp_path):
        """BVA: limit == count → all returned."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        for i in range(3):
            store.log_challenge(_make_challenge(challenge_id=f"chal-{i}"))
        assert len(store.get_challenges(limit=3)) == 3

    def test_bva_limit_less_than_count(self, tmp_path):
        """BVA: limit < count → capped."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        for i in range(3):
            store.log_challenge(_make_challenge(challenge_id=f"chal-{i}"))
        assert len(store.get_challenges(limit=2)) == 2


# ---------------------------------------------------------------------------
# Lines 276-284 — get_challenge_stats
# ---------------------------------------------------------------------------

class TestGetChallengeStats:
    def test_empty_table_returns_zero_rate(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        stats = store.get_challenge_stats()
        assert stats["total"] == 0
        assert stats["accepted"] == 0
        assert stats["acceptance_rate"] == pytest.approx(0.0)

    def test_one_accepted_of_two_non_null(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge(challenge_id="c1"), accepted=True)
        store.log_challenge(_make_challenge(challenge_id="c2"), accepted=False)
        stats = store.get_challenge_stats()
        assert stats["total"] == 2
        assert stats["accepted"] == 1
        assert stats["acceptance_rate"] == pytest.approx(0.5)

    def test_null_accepted_excluded_from_rate(self, tmp_path):
        """Challenges with accepted=None are excluded from stats."""
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge(challenge_id="c1"), accepted=True)
        store.log_challenge(_make_challenge(challenge_id="c2"), accepted=None)  # excluded
        store.log_challenge(_make_challenge(challenge_id="c3"), accepted=None)  # excluded
        stats = store.get_challenge_stats()
        assert stats["total"] == 1  # only non-NULL rows counted
        assert stats["accepted"] == 1
        assert stats["acceptance_rate"] == pytest.approx(1.0)

    def test_three_challenges_one_third_accepted(self, tmp_path):
        store = TradeStore(db_path=str(tmp_path / "trades.db"))
        store.log_challenge(_make_challenge(challenge_id="c1"), accepted=True)
        store.log_challenge(_make_challenge(challenge_id="c2"), accepted=False)
        store.log_challenge(_make_challenge(challenge_id="c3"), accepted=False)
        stats = store.get_challenge_stats()
        assert stats["total"] == 3
        assert stats["acceptance_rate"] == pytest.approx(1 / 3)
