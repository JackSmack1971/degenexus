"""SQLite-backed trade history store. Source of Truth for all trade records."""

from __future__ import annotations
import sqlite3
import json
import os
import logging
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TradeStore:
    """
    Persistent trade history in SQLite.
    All writes use WAL mode for crash safety.
    All reads return dicts or None — no ORM objects.
    """

    def __init__(self, db_path: str = "memory/trading_history.db") -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS trades (
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
                    partial_pnl REAL DEFAULT 0.0,
                    realized_pnl REAL,
                    realized_pnl_pct REAL,
                    risk_score REAL,
                    agent_reasoning TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    trend TEXT,
                    confidence REAL,
                    signal_strength TEXT,
                    reasoning TEXT,
                    data_quality TEXT,
                    generated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS agent_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    cycle_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS challenge_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    challenge_id TEXT NOT NULL,
                    challenger TEXT NOT NULL,
                    challenged_agent TEXT NOT NULL,
                    disputed_field TEXT NOT NULL,
                    evidence TEXT,
                    accepted INTEGER,
                    timestamp TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);
                CREATE INDEX IF NOT EXISTS idx_trades_state ON trades(state);
                CREATE INDEX IF NOT EXISTS idx_trades_closed_at ON trades(closed_at);
            """)
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(trades)").fetchall()
            }
            if "partial_pnl" not in columns:
                conn.execute(
                    "ALTER TABLE trades ADD COLUMN partial_pnl REAL DEFAULT 0.0"
                )

    # ── Trades ──────────────────────────────────────────────────────────────

    def upsert_trade(self, trade) -> None:
        """Insert or update a trade record."""
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO trades VALUES (
                    :trade_id, :proposal_id, :signal_id, :symbol, :direction,
                    :state, :order_type, :entry_price, :fill_price, :slippage_pct,
                    :shares, :stop_loss, :take_profit, :max_loss_usd, :risk_reward_ratio,
                    :close_price, :close_reason, :partial_pnl, :realized_pnl, :realized_pnl_pct,
                    :risk_score, :agent_reasoning, :opened_at, :closed_at, :created_at
                ) ON CONFLICT(trade_id) DO UPDATE SET
                    state=excluded.state,
                    fill_price=excluded.fill_price,
                    slippage_pct=excluded.slippage_pct,
                    close_price=excluded.close_price,
                    close_reason=excluded.close_reason,
                    partial_pnl=excluded.partial_pnl,
                    realized_pnl=excluded.realized_pnl,
                    realized_pnl_pct=excluded.realized_pnl_pct,
                    opened_at=excluded.opened_at,
                    closed_at=excluded.closed_at,
                    agent_reasoning=excluded.agent_reasoning
            """, {
                "trade_id": trade.trade_id,
                "proposal_id": trade.proposal_id,
                "signal_id": trade.signal_id,
                "symbol": trade.symbol,
                "direction": trade.direction.value if hasattr(trade.direction, 'value') else str(trade.direction),
                "state": trade.state.value if hasattr(trade.state, 'value') else str(trade.state),
                "order_type": trade.order_type.value if hasattr(trade.order_type, 'value') else str(trade.order_type),
                "entry_price": trade.entry_price,
                "fill_price": trade.fill_price,
                "slippage_pct": trade.slippage_pct,
                "shares": trade.shares,
                "stop_loss": trade.stop_loss,
                "take_profit": trade.take_profit,
                "max_loss_usd": trade.max_loss_usd,
                "risk_reward_ratio": trade.risk_reward_ratio,
                "close_price": trade.close_price,
                "close_reason": trade.close_reason.value if trade.close_reason and hasattr(trade.close_reason, 'value') else str(trade.close_reason) if trade.close_reason else None,
                "partial_pnl": trade.partial_pnl,
                "realized_pnl": trade.realized_pnl,
                "realized_pnl_pct": trade.realized_pnl_pct,
                "risk_score": trade.risk_score,
                "agent_reasoning": json.dumps(trade.agent_reasoning),
                "opened_at": trade.opened_at.isoformat() if trade.opened_at else None,
                "closed_at": trade.closed_at.isoformat() if trade.closed_at else None,
                "created_at": trade.created_at.isoformat(),
            })

    def get_closed_trades(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE state='CLOSED' ORDER BY closed_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_trades(self, n: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE state IN ('CLOSED','REJECTED','DROPPED') "
                "ORDER BY created_at DESC LIMIT ?",
                (n,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_trades_by_symbol(self, symbol: str, limit: int = 20) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM trades WHERE symbol=? AND state='CLOSED' "
                "ORDER BY closed_at DESC LIMIT ?",
                (symbol, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Agent decisions ──────────────────────────────────────────────────────

    def log_agent_message(
        self, session_id: str, cycle_id: str, agent_id: str,
        message_type: str, payload: dict
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO agent_decisions (session_id, cycle_id, agent_id, message_type, payload, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, cycle_id, agent_id, message_type,
                 json.dumps(payload), datetime.now(timezone.utc).isoformat())
            )

    # ── Challenges ──────────────────────────────────────────────────────────

    def log_challenge(self, challenge, accepted: Optional[bool] = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO challenge_log "
                "(challenge_id, challenger, challenged_agent, disputed_field, evidence, accepted, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    challenge.challenge_id,
                    challenge.challenger,
                    challenge.challenged_agent,
                    challenge.disputed_field,
                    json.dumps(challenge.evidence),
                    int(accepted) if accepted is not None else None,
                    datetime.now(timezone.utc).isoformat(),
                )
            )

    def log_counter_challenge(
        self,
        challenge_id: str,
        proposal_id: str,
        challenger: str,
        challenged_agent: str,
        reasoning: str,
    ) -> None:
        """Log a CEO counter-challenge against a risk rejection."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO challenge_log "
                "(challenge_id, challenger, challenged_agent, disputed_field, evidence, accepted, timestamp) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    challenge_id,
                    challenger,
                    challenged_agent,
                    f"risk_rejection:{proposal_id}",
                    json.dumps({"reasoning": reasoning}),
                    None,
                    datetime.now(timezone.utc).isoformat(),
                )
            )

    def resolve_challenge(self, challenge_id: str, accepted: bool) -> None:
        """Update a challenge's outcome after re-evaluation."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE challenge_log SET accepted=? WHERE challenge_id=?",
                (int(accepted), challenge_id)
            )

    def get_challenges(self, limit: int = 20) -> list[dict]:
        """Read challenge history, most recent first."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM challenge_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_challenge_stats(self) -> dict:
        """Summary: total challenges, acceptance rate."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as total, "
                "SUM(CASE WHEN accepted=1 THEN 1 ELSE 0 END) as accepted "
                "FROM challenge_log WHERE accepted IS NOT NULL"
            ).fetchone()
            total = row["total"] or 0
            accepted = row["accepted"] or 0
            return {
                "total": total,
                "accepted": accepted,
                "acceptance_rate": accepted / total if total > 0 else 0.0,
            }
