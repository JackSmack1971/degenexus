"""Builds performance summary strings injected into agent system prompts."""

from __future__ import annotations
from .performance import PerformanceStats


class ContextInjector:
    """
    Converts PerformanceStats into human-readable context strings
    that agents receive at the start of each cycle.
    This is the adaptation mechanism — no ML required.
    """

    def build_context(
        self,
        stats: PerformanceStats,
        portfolio_snapshot=None,
        risk_limits=None,
        consecutive_losses: int = 0,
        watchlist: list | None = None,
        open_positions_summary: str = "",
    ) -> str:
        if stats.total_trades == 0:
            return self._empty_context()

        streak_str = self._streak_string(stats.current_streak)
        pf_str = f"{stats.profit_factor:.2f}" if stats.profit_factor != float("inf") else "∞"

        lines = [
            "=== PERFORMANCE CONTEXT (injected by Memory System) ===",
            f"Trades analysed: last {stats.closed_trades} closed",
            f"Win Rate: {stats.win_rate:.1%}  |  Profit Factor: {pf_str}",
            f"Avg Win: ${stats.avg_win_usd:.2f}  |  Avg Loss: ${stats.avg_loss_usd:.2f}",
            f"Total P&L: ${stats.total_pnl:+.2f}",
            f"Current streak: {streak_str}",
        ]

        if stats.best_symbol:
            lines.append(f"Strongest symbol: {stats.best_symbol} "
                         f"(P&L: ${stats.symbol_stats[stats.best_symbol]['pnl']:+.2f})")

        if stats.worst_symbol and stats.worst_symbol != stats.best_symbol:
            lines.append(f"Weakest symbol:   {stats.worst_symbol} "
                         f"(P&L: ${stats.symbol_stats[stats.worst_symbol]['pnl']:+.2f}) "
                         "— consider tighter criteria")

        if portfolio_snapshot:
            lines += [
                "",
                "=== PORTFOLIO STATE ===",
                f"Total value: ${portfolio_snapshot.total_value:,.2f}",
                f"Cash:        ${portfolio_snapshot.cash:,.2f}",
                f"Invested:    ${portfolio_snapshot.invested:,.2f}",
                f"Drawdown:    {portfolio_snapshot.drawdown_pct:.2%}",
                f"Open positions: {portfolio_snapshot.open_positions_count}",
            ]

        if risk_limits is not None and portfolio_snapshot is not None:
            exposure_pct = (
                portfolio_snapshot.invested / portfolio_snapshot.total_value
                if portfolio_snapshot.total_value > 0 else 0.0
            )
            lines += [
                "",
                "=== RISK CAPACITY ===",
                f"Max loss/trade: {risk_limits.max_loss_pct_per_trade:.1%}  |  "
                f"Max positions: {risk_limits.max_open_positions} "
                f"(current: {portfolio_snapshot.open_positions_count})  |  "
                f"Max exposure: {risk_limits.max_total_exposure_pct:.0%} "
                f"(current: {exposure_pct:.1%})",
                f"Policy thresholds — Min confidence: {risk_limits.min_confidence:.0%}  |  "
                f"Min R:R: {risk_limits.min_risk_reward}  |  "
                f"Consecutive-loss cooldown: {risk_limits.max_consecutive_losses} "
                f"(current streak: {consecutive_losses})",
                "=== END RISK CAPACITY ===",
            ]

        if stats.risk_manager_veto_rate > 0:
            approval_rate = 1.0 - stats.risk_manager_veto_rate
            lines.append(f"Risk Manager approval rate: {approval_rate:.0%} "
                         f"({'healthy' if approval_rate >= 0.5 else 'low — consider raising signal quality'})")

        if watchlist and stats.symbol_stats:
            sym_lines = ["", "=== WATCHLIST PERFORMANCE ==="]
            for sym in watchlist:
                s = stats.symbol_stats.get(sym)
                if s and s["trades"] > 0:
                    win_rate = s["wins"] / s["trades"]
                    sym_lines.append(
                        f"  {sym}: {s['wins']}/{s['trades']} wins ({win_rate:.0%}) | "
                        f"P&L: ${s['pnl']:+.2f}"
                    )
                else:
                    sym_lines.append(f"  {sym}: no history yet")
            lines += sym_lines

        if open_positions_summary and open_positions_summary != "No open positions.":
            lines += ["", "=== CURRENT OPEN POSITIONS ===", open_positions_summary]

        if stats.current_streak <= -2:
            lines.append(
                "\n⚠ CAUTION: Multiple consecutive losses detected. "
                "Raise conviction threshold before next trade."
            )

        lines.append("=== END CONTEXT ===")
        return "\n".join(lines)

    def _empty_context(self) -> str:
        return (
            "=== PERFORMANCE CONTEXT ===\n"
            "No trade history yet. This is the first session.\n"
            "Apply standard analysis criteria.\n"
            "=== END CONTEXT ==="
        )

    def _streak_string(self, streak: int) -> str:
        if streak > 0:
            return f"+{streak} wins in a row"
        if streak < 0:
            return f"{abs(streak)} losses in a row"
        return "neutral"
