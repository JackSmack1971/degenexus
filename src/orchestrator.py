"""
CEO Agent + Debate Cycle Orchestrator.
Coordinates the full 8-phase debate cycle per the architectural plan.
"""

from __future__ import annotations
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Callable

from .agents.ceo_agent import CEOAgent
from .agents.data_analyst import DataAnalystAgent
from .agents.quant_agent import QuantAgent
from .agents.risk_manager import RiskManagerAgent
from .agents.execution_agent import ExecutionAgent
from .agents.portfolio_manager import PortfolioManagerAgent
from .core.portfolio import Portfolio
from .core.risk_gate import RiskGate
from .models.signals import MarketSignal, TradeProposal, RiskDecision
from .models.trade import Trade, Position, Direction
from .models.messages import AgentID
from .memory.trade_store import TradeStore
from .memory.performance import PerformanceAnalytics
from .memory.context_injector import ContextInjector

logger = logging.getLogger(__name__)


class DebateEvent:
    def __init__(self, event_type: str, agent: str, content: str) -> None:
        self.event_type = event_type
        self.agent = agent
        self.content = content
        self.timestamp = datetime.now(timezone.utc)


class TradingOrchestrator:
    """
    Runs the 8-phase debate cycle:
    SCAN → CEO_TRIAGE → QUANT_DESIGN → RISK_EVALUATE → CEO_FINAL → EXECUTE → MONITOR → LEARN
    """

    MAX_CHALLENGE_ROUNDS = 2

    def __init__(
        self,
        watchlist: list[str],
        event_callback: Optional[Callable[[DebateEvent], None]] = None,
    ) -> None:
        self.watchlist = watchlist
        self.event_callback = event_callback or (lambda e: None)
        self.session_id = str(uuid.uuid4())

        self.portfolio = Portfolio()
        self.risk_gate = RiskGate()
        self.trade_store = TradeStore()
        self.performance = PerformanceAnalytics()
        self.context_injector = ContextInjector()

        context = self._build_context()

        self.ceo = CEOAgent(context)
        self.analyst = DataAnalystAgent(context)
        self.quant = QuantAgent(context)
        self.risk_manager = RiskManagerAgent(self.risk_gate, context)
        self.execution = ExecutionAgent(context)
        self.portfolio_manager = PortfolioManagerAgent(
            self.portfolio,
            context,
            event_callback=self._pm_event,
        )

        self._cycle_count = 0
        self._debate_log: list[DebateEvent] = []

    # ── Public interface ─────────────────────────────────────────────────────

    def run_cycle(self) -> dict:
        """
        Execute one complete debate cycle.
        Returns summary dict with cycle metrics.
        """
        self._cycle_count += 1
        cycle_id = f"cycle-{self._cycle_count:04d}"
        self._debate_log.clear()

        self._emit("CYCLE_START", "SYSTEM", f"Cycle {self._cycle_count} | Watchlist: {self.watchlist}")

        # Phase 1: Monitor existing positions
        closed_this_cycle = self.portfolio_manager.monitor_cycle()
        for ct in closed_this_cycle:
            self.trade_store.upsert_trade(ct)
            self._emit("POSITION_CLOSED", "PORTFOLIO_MANAGER",
                       f"{ct.symbol} closed | {ct.close_reason.value} | PnL: ${ct.realized_pnl:+.2f}")

        # Update performance context every cycle
        context = self._build_context()
        for agent in [self.ceo, self.analyst, self.quant, self.risk_manager, self.execution]:
            agent.update_context(context)

        # Phase 2: Scan signals
        signals = self._phase_scan()
        if not signals:
            self._emit("NO_SIGNALS", "CEO", "No signals above threshold this cycle")
            return self._cycle_summary(cycle_id, trades_opened=0)

        # Phase 3: CEO triage
        selected_signals = self._phase_ceo_triage(signals)
        if not selected_signals:
            self._emit("NO_APPROVED_SIGNALS", "CEO", "No signals approved after triage")
            return self._cycle_summary(cycle_id, trades_opened=0)

        # Phases 4-7 per signal
        trades_opened = 0
        for signal in selected_signals[:2]:
            opened = self._phase_trade_cycle(signal)
            if opened:
                trades_opened += 1

        return self._cycle_summary(cycle_id, trades_opened=trades_opened)

    # ── Phases ───────────────────────────────────────────────────────────────

    def _phase_scan(self) -> list[MarketSignal]:
        signals = []
        for symbol in self.watchlist:
            self._emit("SCANNING", "DATA_ANALYST", f"Analyzing {symbol}...")
            signal = self.analyst.analyze(symbol)
            if signal:
                signals.append(signal)
                self._emit("SIGNAL", "DATA_ANALYST",
                            f"{signal.symbol}: {signal.direction} | "
                            f"{signal.trend.value} | conf={signal.confidence:.2f} | "
                            f"{signal.reasoning[:80]}...")

        return sorted(signals, key=lambda s: s.confidence, reverse=True)

    def _phase_ceo_triage(self, signals: list[MarketSignal]) -> list[MarketSignal]:
        if not signals:
            return []

        open_count = self.portfolio.open_positions_count
        selected = []
        for signal in signals[:3]:
            decision = self.ceo.triage_signal(signal, open_count)
            if decision == "PROCEED":
                selected.append(signal)
                self._emit("CEO_APPROVED_SIGNAL", "CEO",
                           f"{signal.symbol} signal approved for proposal stage")
            else:
                self._emit("CEO_REJECTED_SIGNAL", "CEO",
                           f"{signal.symbol} signal rejected at triage")

        return selected

    def _phase_trade_cycle(self, signal: MarketSignal) -> bool:
        """Phases 4-7 for a single signal. Returns True if trade opened."""

        # Phase 4: Quant design
        stats = self.performance.compute(self.trade_store.get_recent_trades(50))
        proposal = self.quant.design_proposal(
            signal=signal,
            portfolio_value=self.portfolio.total_value,
            available_cash=self.portfolio.cash,
            win_rate=stats.win_rate if stats.win_rate > 0 else 0.55,
            avg_win_usd=stats.avg_win_usd,
            avg_loss_usd=stats.avg_loss_usd,
        )

        if proposal is None:
            self._emit("QUANT_FAILED", "QUANT", f"No viable proposal for {signal.symbol}")
            return False

        self._emit("PROPOSAL", "QUANT",
                   f"{signal.symbol}: {proposal.direction} {proposal.position_size_shares}sh "
                   f"@ ${proposal.entry_price:.2f} | "
                   f"SL:${proposal.stop_loss:.2f} TP:${proposal.take_profit:.2f} | "
                   f"R:R {proposal.risk_reward_ratio:.2f}")

        # Phase 5a: Hard gate (deterministic, instantaneous — no LLM)
        open_summary = self.portfolio_manager.open_trades_summary()
        violations = self.risk_gate.check_hard_rules(
            proposal=proposal,
            portfolio_value=self.portfolio.total_value,
            open_positions_count=self.portfolio.open_positions_count,
            total_exposure_usd=self.portfolio.total_exposure_usd,
        )
        if violations:
            risk_decision = self.risk_gate.build_rejection(proposal, violations)
            self._emit("RISK_HARD_REJECTED", "RISK_MANAGER",
                       f"{signal.symbol} HARD REJECTED | {'; '.join(violations)}")
        else:
            # Phase 5b: Contextual LLM assessment (only reached if hard rules pass)
            risk_decision = self.risk_manager.assess_contextual_risk(
                proposal=proposal,
                consecutive_losses=self.portfolio.consecutive_losses,
                signal_confidence=signal.confidence,
                open_positions_summary=open_summary,
            )

        if risk_decision.approved:
            conditions_str = f" | conditions: {risk_decision.conditions}" if risk_decision.conditions else ""
            self._emit("RISK_APPROVED", "RISK_MANAGER",
                       f"{signal.symbol} APPROVED | score: {risk_decision.risk_score:.1f}/10 | "
                       f"R:R {proposal.risk_reward_ratio:.2f}{conditions_str}")
        else:
            self._emit("RISK_REJECTED", "RISK_MANAGER",
                       f"{signal.symbol} REJECTED | {risk_decision.risk_reasoning}")

            if self._ceo_counter_challenge(signal, proposal, risk_decision):
                challenge_id = str(uuid.uuid4())
                self.trade_store.log_counter_challenge(
                    challenge_id=challenge_id,
                    proposal_id=proposal.proposal_id,
                    challenger="CEO",
                    challenged_agent="RISK_MANAGER",
                    reasoning=signal.reasoning,
                )
                self._emit("CEO_CHALLENGE", "CEO",
                           f"CEO counter-challenges risk rejection for {signal.symbol}")
                risk_decision = self.risk_manager.assess_contextual_risk(
                    proposal=proposal,
                    consecutive_losses=self.portfolio.consecutive_losses,
                    signal_confidence=signal.confidence,
                    open_positions_summary=f"CEO challenge context: {signal.reasoning}",
                )
                self.trade_store.resolve_challenge(challenge_id, risk_decision.approved)
                if risk_decision.approved:
                    self._emit("RISK_REVERSED", "RISK_MANAGER",
                               f"{signal.symbol} approved after CEO challenge")
                else:
                    self._emit("RISK_FINAL", "RISK_MANAGER",
                               f"{signal.symbol} veto maintained — trade blocked")
                    return False
            else:
                return False

        # Phase 6: CEO final decision
        self._emit("CEO_FINAL", "CEO", f"{signal.symbol} — PROCEED to execution")

        # Phase 7: Execution
        current_price = signal.current_price
        trade, fill, error = self.execution.execute(proposal, risk_decision, current_price)

        if error or trade is None:
            self._emit("EXECUTION_FAILED", "EXECUTION", f"{signal.symbol}: {error}")
            return False

        # Register with portfolio manager
        position = Position(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            direction=trade.direction,
            shares=trade.shares,
            entry_price=trade.fill_price,
            current_price=current_price,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit,
        )
        self.portfolio_manager.register_trade(trade, position)
        self.trade_store.upsert_trade(trade)

        self._emit("TRADE_OPENED", "EXECUTION",
                   f"{trade.direction.value} {trade.symbol} "
                   f"{trade.shares}sh @ ${trade.fill_price:.4f} "
                   f"(slip: {trade.slippage_pct*100:.3f}%) | "
                   f"SL:${trade.stop_loss:.2f} TP:${trade.take_profit:.2f}")

        return True

    def _ceo_counter_challenge(
        self,
        signal: MarketSignal,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
    ) -> bool:
        """Hard rule violations are never challengeable. Otherwise defer to CEO LLM judgment."""
        if not risk_decision.hard_rules_passed:
            return False
        return self.ceo.decide_counter_challenge(signal, proposal, risk_decision)

    # ── Utilities ────────────────────────────────────────────────────────────

    def _build_context(self) -> str:
        trades = self.trade_store.get_recent_trades(50)
        stats = self.performance.compute(trades)
        snapshot = self.portfolio.snapshot() if hasattr(self, "portfolio") else None
        open_positions = (
            self.portfolio_manager.open_trades_summary()
            if hasattr(self, "portfolio_manager") else ""
        )
        return self.context_injector.build_context(
            stats,
            snapshot,
            risk_limits=self.risk_gate.limits,
            consecutive_losses=self.portfolio.consecutive_losses if hasattr(self, "portfolio") else 0,
            watchlist=self.watchlist,
            open_positions_summary=open_positions,
        )

    def _emit(self, event_type: str, agent: str, content: str) -> None:
        event = DebateEvent(event_type=event_type, agent=agent, content=content)
        self._debate_log.append(event)
        self.event_callback(event)

    def _pm_event(self, event_type: str, content: str) -> None:
        """Bridge: translates PortfolioManager callbacks into the main event stream."""
        self._emit(event_type, "PORTFOLIO_MANAGER", content)

    def _cycle_summary(self, cycle_id: str, trades_opened: int) -> dict:
        snapshot = self.portfolio.snapshot()
        return {
            "cycle_id": cycle_id,
            "cycle_number": self._cycle_count,
            "trades_opened": trades_opened,
            "portfolio_value": snapshot.total_value,
            "cash": snapshot.cash,
            "total_pnl": self.portfolio.total_pnl,
            "total_pnl_pct": self.portfolio.total_pnl_pct,
            "open_positions": snapshot.open_positions_count,
            "win_count": snapshot.win_count,
            "loss_count": snapshot.loss_count,
            "drawdown_pct": snapshot.drawdown_pct,
            "debate_events": len(self._debate_log),
        }

    @property
    def debate_log(self) -> list[DebateEvent]:
        return list(self._debate_log)
