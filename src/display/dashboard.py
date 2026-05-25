"""Rich live console dashboard for the AI Trading Company."""

from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.style import Style
from rich import box

from .trade_feed import TradeFeed
from ..orchestrator import TradingOrchestrator, DebateEvent


class Dashboard:
    """
    Full-screen Rich terminal dashboard.
    Layout:
      ┌─────────────────────────────────┐
      │         HEADER (title + time)   │
      ├────────────────┬────────────────┤
      │  PORTFOLIO     │  AGENT FEED    │
      ├────────────────┴────────────────┤
      │  OPEN POSITIONS                 │
      ├─────────────────────────────────┤
      │  LAST CLOSED TRADES             │
      └─────────────────────────────────┘
    """

    def __init__(self, orchestrator: TradingOrchestrator) -> None:
        self.orchestrator = orchestrator
        self.console = Console()
        self.feed = TradeFeed(max_events=15)
        self._last_cycle: dict = {}
        self._closed_history: list[dict] = []

    def on_event(self, event: DebateEvent) -> None:
        self.feed.push(event.event_type, event.agent, event.content)

    def run(self, cycle_delay_seconds: float = 5.0, max_cycles: int = 0) -> None:
        """Run the trading loop with live dashboard."""
        self.orchestrator.event_callback = self.on_event

        with Live(
            self._build_layout(),
            console=self.console,
            refresh_per_second=2,
            screen=True,
        ) as live:
            cycle = 0
            while True:
                cycle += 1
                if max_cycles > 0 and cycle > max_cycles:
                    break

                summary = self.orchestrator.run_cycle()
                self._last_cycle = summary

                closed_trades = self.orchestrator.portfolio_manager.portfolio.closed_trades
                self._closed_history = [
                    {
                        "symbol": t.symbol,
                        "direction": t.direction.value,
                        "shares": t.shares,
                        "pnl": t.realized_pnl,
                        "reason": t.close_reason.value if t.close_reason else "?",
                    }
                    for t in closed_trades[-5:]
                ]

                live.update(self._build_layout())
                time.sleep(cycle_delay_seconds)

    def _build_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="middle", size=10),
            Layout(name="positions", size=8),
            Layout(name="closed", size=8),
            Layout(name="debate", minimum_size=8),
        )
        layout["middle"].split_row(
            Layout(name="portfolio", ratio=1),
            Layout(name="agentfeed", ratio=2),
        )

        layout["header"].update(self._render_header())
        layout["portfolio"].update(self._render_portfolio())
        layout["agentfeed"].update(self._render_agent_feed())
        layout["positions"].update(self._render_positions())
        layout["closed"].update(self._render_closed())
        layout["debate"].update(self.feed.render_table())

        return layout

    def _render_header(self) -> Panel:
        port = self.orchestrator.portfolio
        pnl = port.total_pnl
        pnl_pct = port.total_pnl_pct
        pnl_color = "green" if pnl >= 0 else "red"
        sign = "+" if pnl >= 0 else ""

        title = Text()
        title.append("  ⬡  AI TRADING COMPANY  ⬡  ", style="bold gold1")
        title.append(f"  Capital: ${port.total_value:,.2f}  ", style="bold white")
        title.append(
            f"P&L: {sign}${pnl:.2f} ({sign}{pnl_pct:.2%})  ",
            style=f"bold {pnl_color}",
        )
        title.append(
            f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            style="dim",
        )
        return Panel(title, border_style="gold1", height=3)

    def _render_portfolio(self) -> Panel:
        port = self.orchestrator.portfolio
        snap = port.snapshot()

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="dim", width=16)
        table.add_column("Value", style="bold white")

        table.add_row("Cash:", f"${snap.cash:,.2f}")
        table.add_row("Invested:", f"${snap.invested:,.2f}")
        table.add_row("Drawdown:", f"{snap.drawdown_pct:.2%}")
        table.add_row("Open pos:", str(snap.open_positions_count))
        table.add_row("Wins / Losses:", f"{snap.win_count} / {snap.loss_count}")
        table.add_row("Cycle:", str(self.orchestrator._cycle_count))

        return Panel(table, title="PORTFOLIO", border_style="cyan", height=10)

    def _render_agent_feed(self) -> Panel:
        last_events = self.orchestrator.debate_log[-6:]
        lines = []
        from .trade_feed import AGENT_COLORS, EVENT_ICONS
        for ev in last_events:
            icon = EVENT_ICONS.get(ev.event_type, "·")
            color = AGENT_COLORS.get(ev.agent, "white")
            lines.append(Text.assemble(
                (f"[{ev.agent}] ", color),
                (f"{icon} {ev.content[:70]}", "white"),
            ))

        text = Text("\n").join(lines) if lines else Text("Waiting for first cycle...", style="dim")
        return Panel(text, title="AGENT ACTIVITY", border_style="yellow", height=10)

    def _render_positions(self) -> Panel:
        positions = self.orchestrator.portfolio.open_positions
        if not positions:
            return Panel(
                Text("No open positions.", style="dim"),
                title="OPEN POSITIONS",
                border_style="blue",
                height=8,
            )

        table = Table(show_header=True, header_style="bold white", box=box.SIMPLE, expand=True)
        table.add_column("Symbol", width=6)
        table.add_column("Dir", width=5)
        table.add_column("Shares", width=7)
        table.add_column("Entry", width=10)
        table.add_column("Current", width=10)
        table.add_column("SL", width=10)
        table.add_column("TP", width=10)
        table.add_column("UnrPnL", width=12)

        for pos in list(positions.values())[:4]:
            pnl = pos.unrealized_pnl
            pnl_color = "green" if pnl >= 0 else "red"
            table.add_row(
                pos.symbol,
                pos.direction.value,
                str(pos.shares),
                f"${pos.entry_price:.2f}",
                f"${pos.current_price:.2f}" if pos.current_price else "?",
                f"${pos.stop_loss:.2f}",
                f"${pos.take_profit:.2f}",
                Text(f"${pnl:+.2f}", style=f"bold {pnl_color}"),
            )

        return Panel(table, title="OPEN POSITIONS", border_style="blue", height=8)

    def _render_closed(self) -> Panel:
        if not self._closed_history:
            return Panel(
                Text("No closed trades yet.", style="dim"),
                title="LAST 5 CLOSED",
                border_style="dim",
                height=8,
            )

        table = Table(show_header=True, header_style="bold white", box=box.SIMPLE, expand=True)
        table.add_column("Symbol", width=6)
        table.add_column("Dir", width=5)
        table.add_column("Shares", width=7)
        table.add_column("P&L", width=12)
        table.add_column("Reason", width=15)
        table.add_column("Result", width=8)

        for t in self._closed_history[-5:]:
            pnl = t.get("pnl") or 0.0
            pnl_color = "green" if pnl >= 0 else "red"
            result = "WIN" if pnl > 0 else "LOSS"
            table.add_row(
                t.get("symbol", "?"),
                t.get("direction", "?"),
                str(t.get("shares", 0)),
                Text(f"${pnl:+.2f}", style=f"bold {pnl_color}"),
                t.get("reason", "?"),
                Text(result, style=f"bold {pnl_color}"),
            )

        return Panel(table, title="LAST 5 CLOSED TRADES", border_style="dim", height=8)
