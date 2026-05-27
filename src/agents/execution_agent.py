"""
Execution Agent — places simulated orders.
Cannot execute without a valid RiskDecision from the ExecutionGate.
"""

from __future__ import annotations
import logging
import re
from typing import Optional

from .base_agent import BaseAgent
from ..models.signals import TradeProposal, RiskDecision
from ..models.trade import Trade, Fill, TradeState, Direction, OrderType
from ..core.execution_gate import ExecutionGate, TradeBlockedError
from ..core.slippage import SlippageModel, select_order_type
from ..core.trade_lifecycle import TradeLifecycle

logger = logging.getLogger(__name__)


class ExecutionAgent(BaseAgent):

    def __init__(self, performance_context: str = "") -> None:
        super().__init__("EXECUTION", performance_context)
        self.gate = ExecutionGate()
        self.slippage = SlippageModel()
        self.lifecycle = TradeLifecycle()

    def execute(
        self,
        proposal: TradeProposal,
        risk_decision: Optional[RiskDecision],
        current_price: float,
    ) -> tuple[Optional[Trade], Optional[Fill], Optional[str]]:
        """
        Returns (trade, fill, error_reason).
        On any block: (None, None, reason).
        Gate check is the first thing — no execution without valid approval.
        """
        # Hard gate — raises TradeBlockedError if not approved
        try:
            self.gate.validate(proposal, risk_decision)
        except TradeBlockedError as e:
            logger.warning("EXECUTION_GATE blocked trade %s: %s", proposal.proposal_id, e.reason)
            return None, None, e.reason

        # gate.validate() raises TradeBlockedError on None/rejected — assert narrows type for mypy
        assert risk_decision is not None
        effective_proposal = self._apply_conditions(proposal, risk_decision)

        # Determine order type
        if current_price > 0:
            distance_pct = abs(current_price - effective_proposal.entry_price) / current_price
        else:
            distance_pct = 0.05
        order_type_str = select_order_type(
            signal_confidence=0.7,
            price_distance_pct=distance_pct,
        )

        fill_price, slippage_pct = self.slippage.apply_to_price(
            price=effective_proposal.entry_price,
            direction=effective_proposal.direction,
            order_value_usd=effective_proposal.position_value_usd,
        )

        trade = Trade(
            proposal_id=effective_proposal.proposal_id,
            signal_id=effective_proposal.signal_id,
            symbol=effective_proposal.symbol,
            direction=Direction(effective_proposal.direction),
            state=TradeState.CEO_APPROVED,
            order_type=OrderType(order_type_str),
            entry_price=effective_proposal.entry_price,
            fill_price=fill_price,
            slippage_pct=slippage_pct,
            shares=effective_proposal.position_size_shares,
            gross_value=fill_price * effective_proposal.position_size_shares,
            stop_loss=effective_proposal.stop_loss,
            take_profit=effective_proposal.take_profit,
            max_loss_usd=effective_proposal.max_loss_usd,
            risk_reward_ratio=effective_proposal.risk_reward_ratio,
            risk_score=risk_decision.risk_score if risk_decision else 5.0,
            agent_reasoning={
                "quant": effective_proposal.reasoning,
                "risk": risk_decision.risk_reasoning if risk_decision else "",
                "conditions": risk_decision.conditions if risk_decision else [],
            },
        )

        trade = self.lifecycle.transition(trade, TradeState.QUEUED)
        trade = self.lifecycle.open_trade(trade, fill_price, slippage_pct)

        fill = Fill(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            direction=Direction(effective_proposal.direction),
            order_type=OrderType(order_type_str),
            requested_price=effective_proposal.entry_price,
            fill_price=fill_price,
            slippage_pct=slippage_pct,
            shares=effective_proposal.position_size_shares,
            gross_value=trade.gross_value,
            status="FILLED",
        )

        logger.info(
            "EXECUTED: %s %s %d shares @ $%.4f (slip: %.3f%%)",
            trade.direction.value,
            trade.symbol,
            trade.shares,
            fill_price,
            slippage_pct * 100,
        )
        return trade, fill, None

    def _apply_conditions(
        self, proposal: TradeProposal, risk_decision: RiskDecision
    ) -> TradeProposal:
        """Apply any conditions from the Risk Manager (e.g., reduce size)."""
        if not risk_decision.conditions:
            return proposal

        adjusted = proposal.model_copy(deep=True)
        for condition in risk_decision.conditions:
            c = condition.lower()
            if "reduce_size" in c or "reduce size" in c:
                factor = self._parse_size_factor(c)
                adjusted.position_size_shares = max(1, int(adjusted.position_size_shares * factor))
                adjusted.position_value_usd = adjusted.entry_price * adjusted.position_size_shares
                adjusted.max_loss_usd = abs(adjusted.entry_price - adjusted.stop_loss) * adjusted.position_size_shares
                adjusted.max_loss_pct = adjusted.max_loss_usd / adjusted.position_value_usd
                adjusted.portfolio_exposure_pct *= factor
                adjusted.proposal_hash = adjusted.compute_hash()

        return adjusted

    def _parse_size_factor(self, condition: str) -> float:
        match = re.search(r"(\d+)\s*pct", condition.lower())
        if not match:
            return 0.8

        pct = min(int(match.group(1)), 99)
        return 1.0 - (pct / 100.0)

    def _fallback(self, context: str) -> dict:
        return {}
