"""Real-time event log panel for the live dashboard."""

from __future__ import annotations
from collections import deque
from datetime import datetime, timezone

from rich.table import Table
from rich.text import Text


AGENT_COLORS = {
    "CEO": "bold gold1",
    "DATA_ANALYST": "cyan",
    "QUANT": "blue",
    "RISK_MANAGER": "red",
    "EXECUTION": "green",
    "PORTFOLIO_MANAGER": "magenta",
    "MEMORY_SYSTEM": "dim white",
    "SYSTEM": "dim",
}

EVENT_ICONS = {
    "SIGNAL": "📈",
    "SIGNAL_REJECTED": "📉",
    "RISK_APPROVED": "✅",
    "RISK_REJECTED": "🛑",
    "RISK_REVERSED": "🔄",
    "RISK_FINAL": "🔒",
    "TRADE_OPENED": "→",
    "POSITION_CLOSED": "✓",
    "EXECUTION_FAILED": "✗",
    "CEO_APPROVED_SIGNAL": "🔍",
    "CEO_REJECTED_SIGNAL": "✗",
    "CEO_FINAL": "⚡",
    "CEO_CHALLENGE": "⚔",
    "PROPOSAL": "📋",
    "NO_SIGNALS": "—",
    "CYCLE_START": "⬡",
    "QUANT_FAILED": "!",
}


class TradeFeed:
    """Circular buffer of recent debate events for dashboard display."""

    def __init__(self, max_events: int = 15) -> None:
        self._events: deque = deque(maxlen=max_events)

    def push(self, event_type: str, agent: str, content: str) -> None:
        self._events.appendleft({
            "time": datetime.now(timezone.utc).strftime("%H:%M:%S"),
            "event_type": event_type,
            "agent": agent,
            "content": content,
        })

    def render_table(self) -> Table:
        table = Table(
            title="DEBATE LOG",
            show_header=True,
            header_style="bold white",
            border_style="dim white",
            expand=True,
        )
        table.add_column("Time", width=10, style="dim")
        table.add_column("Agent", width=18)
        table.add_column("Event", no_wrap=False)

        for ev in list(self._events):
            icon = EVENT_ICONS.get(ev["event_type"], "·")
            agent_style = AGENT_COLORS.get(ev["agent"], "white")
            agent_text = Text(f"[{ev['agent']}]", style=agent_style)
            event_text = Text(f"{icon}  {ev['content']}")
            table.add_row(ev["time"], agent_text, event_text)

        return table
