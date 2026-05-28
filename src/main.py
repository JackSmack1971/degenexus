"""
AI Trading Company — Entry Point

Usage:
  python src/main.py
  python src/main.py --symbols AAPL,SPY,QQQ --cycles 10
  python src/main.py --symbols NVDA,TSLA --no-dashboard --delay 2
  python src/main.py --list-agents  # print agent registry and exit
"""

from __future__ import annotations
import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI Trading Company — Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/main.py                           # full dashboard, default watchlist
  python src/main.py --symbols AAPL,SPY        # specific symbols
  python src/main.py --cycles 5                # run 5 cycles then exit
  python src/main.py --no-dashboard            # log-only mode
  python src/main.py --delay 30                # 30 seconds between cycles
        """,
    )
    parser.add_argument(
        "--symbols",
        default=os.getenv("WATCHLIST", "AAPL,SPY,QQQ,NVDA"),
        help="Comma-separated watchlist (default: AAPL,SPY,QQQ,NVDA)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=int(os.getenv("MAX_CYCLES", "0")),
        help="Max cycles to run (0 = infinite)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Seconds between cycles (default: 5)",
    )
    parser.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Run without Rich dashboard (log-only mode)",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=float(os.getenv("STARTING_CAPITAL", "10000.00")),
        help="Starting capital (default: $10,000)",
    )
    parser.add_argument(
        "--list-agents",
        action="store_true",
        help="Print agent registry and exit",
    )
    return parser.parse_args()


def list_agents() -> None:
    """Print the agent registry — what each agent does and what LLM it calls."""
    agents = [
        ("CEO", "CEOAgent", "Triages signals (PROCEED/ABORT) and decides counter-challenges against risk rejections"),
        ("DATA_ANALYST", "DataAnalystAgent", "Fetches market data, computes indicators, emits MarketSignal with confidence score"),
        ("QUANT", "QuantAgent", "Sizes positions via half-Kelly criterion, designs TradeProposal with SL/TP"),
        ("RISK_MANAGER", "RiskManagerAgent", "Contextual LLM risk assessment (layer 2); hard rules enforced separately by RiskGate"),
        ("EXECUTION", "ExecutionAgent", "Executes approved proposals, computes fill price with simulated slippage"),
        ("PORTFOLIO_MANAGER", "PortfolioManagerAgent", "Monitors open positions each cycle; triggers partial TP and full TP/SL closures"),
    ]
    print("\nAgent Registry — AI Trading Company\n" + "=" * 50)
    for agent_id, class_name, description in agents:
        print(f"\n  {agent_id} ({class_name})")
        print(f"    {description}")
    print("\nDebate cycle phases:")
    print("  SCAN -> CEO_TRIAGE -> QUANT_DESIGN -> RISK_HARD_GATE -> RISK_EVALUATE -> CEO_FINAL -> EXECUTE -> MONITOR")
    print()


def run_with_dashboard(orchestrator, args) -> None:
    from src.display.dashboard import Dashboard
    dashboard = Dashboard(orchestrator)
    logger.info("Starting AI Trading Company dashboard...")
    dashboard.run(cycle_delay_seconds=args.delay, max_cycles=args.cycles)


def run_without_dashboard(orchestrator, args) -> None:
    import time

    def log_event(event) -> None:
        logger.info("[%s] %s: %s", event.event_type, event.agent, event.content)

    orchestrator.event_callback = log_event

    cycle = 0
    while True:
        cycle += 1
        if args.cycles > 0 and cycle > args.cycles:
            break

        logger.info("=== CYCLE %d ===", cycle)
        summary = orchestrator.run_cycle()
        logger.info(
            "Cycle %d complete | opened: %d | portfolio: $%.2f | PnL: $%+.2f (%.2f%%)",
            cycle,
            summary["trades_opened"],
            summary["portfolio_value"],
            summary["total_pnl"],
            summary["total_pnl_pct"] * 100,
        )
        time.sleep(args.delay)


def main() -> None:
    args = parse_args()

    if args.list_agents:
        list_agents()
        sys.exit(0)

    watchlist = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    if not watchlist:
        logger.error("No valid symbols in watchlist")
        sys.exit(1)

    logger.info(
        "AI Trading Company starting | capital: $%.2f | watchlist: %s",
        args.capital, watchlist,
    )

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning(
            "ANTHROPIC_API_KEY not set — agents will use deterministic fallback mode. "
            "Set the key in .env or environment for LLM-powered analysis."
        )

    from src.orchestrator import TradingOrchestrator
    from src.core.portfolio import Portfolio
    orchestrator = TradingOrchestrator(
        watchlist=watchlist,
        portfolio=Portfolio(starting_capital=args.capital),
    )

    if args.no_dashboard:
        run_without_dashboard(orchestrator, args)
    else:
        try:
            run_with_dashboard(orchestrator, args)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as exc:
            logger.error("Dashboard error: %s — falling back to log mode", exc)
            run_without_dashboard(orchestrator, args)


if __name__ == "__main__":
    main()
