"""Performance analytics computed from trade history."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PerformanceStats:
    total_trades: int = 0
    closed_trades: int = 0
    win_count: int = 0
    loss_count: int = 0
    win_rate: float = 0.0
    avg_win_usd: float = 0.0
    avg_loss_usd: float = 0.0
    profit_factor: float = 0.0
    avg_risk_reward: float = 0.0
    total_pnl: float = 0.0
    max_drawdown_pct: float = 0.0
    best_symbol: str = ""
    worst_symbol: str = ""
    best_signal_type: str = ""
    current_streak: int = 0
    risk_manager_veto_rate: float = 0.0
    avg_holding_bars: float = 0.0
    symbol_stats: dict = field(default_factory=dict)


class PerformanceAnalytics:
    """
    Computes all performance metrics from the trade store.
    Input: list of trade dicts (from TradeStore.get_closed_trades).
    """

    def compute(self, trades: list[dict]) -> PerformanceStats:
        if not trades:
            return PerformanceStats()

        closed = [t for t in trades if t.get("state") == "CLOSED"]
        if not closed:
            return PerformanceStats(total_trades=len(trades))

        wins = [t for t in closed if (t.get("realized_pnl") or 0) > 0]
        losses = [t for t in closed if (t.get("realized_pnl") or 0) <= 0]

        win_count = len(wins)
        loss_count = len(losses)
        total_closed = len(closed)

        win_rate = win_count / total_closed if total_closed > 0 else 0.0

        avg_win = sum(t["realized_pnl"] for t in wins) / win_count if wins else 0.0
        avg_loss = abs(sum(t["realized_pnl"] for t in losses) / loss_count) if losses else 0.0

        gross_profit = sum(t["realized_pnl"] for t in wins)
        gross_loss = abs(sum(t["realized_pnl"] for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        total_pnl = sum(t.get("realized_pnl") or 0 for t in closed)

        rr_values = [t.get("risk_reward_ratio") or 0 for t in closed]
        avg_rr = sum(rr_values) / len(rr_values) if rr_values else 0.0

        current_streak = self._compute_streak(closed)

        symbol_stats = self._compute_symbol_stats(closed)
        best_symbol = max(symbol_stats, key=lambda s: symbol_stats[s]["pnl"], default="")
        worst_symbol = min(symbol_stats, key=lambda s: symbol_stats[s]["pnl"], default="")

        return PerformanceStats(
            total_trades=len(trades),
            closed_trades=total_closed,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_rate,
            avg_win_usd=avg_win,
            avg_loss_usd=avg_loss,
            profit_factor=profit_factor,
            avg_risk_reward=avg_rr,
            total_pnl=total_pnl,
            current_streak=current_streak,
            best_symbol=best_symbol,
            worst_symbol=worst_symbol,
            symbol_stats=symbol_stats,
        )

    def _compute_streak(self, closed: list[dict]) -> int:
        """Positive = win streak; negative = loss streak."""
        if not closed:
            return 0
        sorted_trades = sorted(closed, key=lambda t: t.get("closed_at") or "")
        streak = 0
        last_sign = None
        for t in reversed(sorted_trades):
            pnl = t.get("realized_pnl") or 0
            sign = 1 if pnl > 0 else -1
            if last_sign is None:
                last_sign = sign
                streak = sign
            elif sign == last_sign:
                streak += sign
            else:
                break
        return streak

    def _compute_symbol_stats(self, closed: list[dict]) -> dict:
        stats: dict[str, dict] = {}
        for t in closed:
            sym = t.get("symbol", "UNKNOWN")
            if sym not in stats:
                stats[sym] = {"trades": 0, "wins": 0, "pnl": 0.0}
            stats[sym]["trades"] += 1
            pnl = t.get("realized_pnl") or 0
            stats[sym]["pnl"] += pnl
            if pnl > 0:
                stats[sym]["wins"] += 1
        return stats
