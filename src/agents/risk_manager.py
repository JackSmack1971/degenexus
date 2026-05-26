"""
Risk Manager Agent — LLM contextual assessment layer.
Note: The HARD VETO is in core/risk_gate.py, not here.
This agent provides contextual reasoning AFTER hard rules pass.
"""

from __future__ import annotations
import logging
from .base_agent import BaseAgent
from ..models.signals import TradeProposal, RiskDecision, RiskDecisionType
from ..core.risk_gate import RiskGate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Risk Manager at an AI trading firm.

Hard structural limits have already been checked. Your job: contextual risk assessment.

Assess:
1. Signal quality — confidence and strength justify this trade type?
2. Risk:reward acceptability — is the proposed R:R ratio adequate for current conditions?
3. Market regime suitability — is this a good time for this trade type?
4. Portfolio correlation — are we over-exposed to this direction or symbol?
5. Consecutive losses context — should we reduce size or pause after a losing streak?
6. Any red flags in the proposal reasoning

Policy thresholds (enforce contextually, not mechanically):
- Signal confidence < 0.55: weak signal. Reject unless setup is exceptional (strong trend alignment, clear technical structure, high R:R).
- Risk:Reward ratio < 1.5: unfavorable. Reject unless confidence is high (>= 0.70) and market conditions strongly favour the trade.
- Consecutive losses >= 3: elevated risk environment. Strongly prefer REJECTED or APPROVED_WITH_CONDITIONS(reduce_size_by_50pct). Do not proceed at full size.

Output a risk_score from 0 (minimal risk) to 10 (maximum risk).
Trades with risk_score > 6 should be REJECTED contextually.
approved = true if risk_score <= 6 AND no major red flags.
decision_type: "APPROVED", "APPROVED_WITH_CONDITIONS", or "REJECTED_CONTEXTUAL"

If APPROVED_WITH_CONDITIONS, list the conditions (e.g., ["reduce_size_by_20pct"]).

Respond ONLY with valid JSON. No commentary outside JSON."""


class RiskManagerAgent(BaseAgent):

    def __init__(self, risk_gate: RiskGate, performance_context: str = "") -> None:
        super().__init__("RISK_MANAGER", performance_context)
        self.risk_gate = risk_gate

    def assess_contextual_risk(
        self,
        proposal: TradeProposal,
        consecutive_losses: int,
        signal_confidence: float,
        open_positions_summary: str = "",
    ) -> RiskDecision:
        """
        Contextual LLM assessment only.
        Caller (Orchestrator) is responsible for running the hard gate first.
        """
        template = self.risk_gate.build_approval_template(proposal)
        return self._contextual_assess(
            proposal, template, consecutive_losses, signal_confidence, open_positions_summary
        )

    def _contextual_assess(
        self,
        proposal: TradeProposal,
        template: RiskDecision,
        consecutive_losses: int,
        signal_confidence: float,
        open_positions_summary: str,
    ) -> RiskDecision:
        safe_reasoning = self._sanitize_external_text(proposal.reasoning)
        safe_open_positions = self._sanitize_external_text(open_positions_summary or "  None")
        user_msg = f"""Assess this trade proposal:

PROPOSAL:
  {self.TRUST_BOUNDARY_NOTICE}
  Symbol: {proposal.symbol}
  Direction: {proposal.direction}
  Entry: ${proposal.entry_price:.4f} ({proposal.entry_type})
  Stop Loss: ${proposal.stop_loss:.4f}
  Take Profit: ${proposal.take_profit:.4f}
  Size: {proposal.position_size_shares} shares (${proposal.position_value_usd:,.2f})
  Max Loss: ${proposal.max_loss_usd:.2f} ({proposal.max_loss_pct:.2%})
  R:R Ratio: {proposal.risk_reward_ratio:.2f}
  Portfolio Exposure: {proposal.portfolio_exposure_pct:.2%}
  Quant Reasoning: {safe_reasoning}

SIGNAL CONTEXT:
  Analyst Confidence: {signal_confidence:.2f}
  Consecutive Losses: {consecutive_losses}

OPEN POSITIONS:
{safe_open_positions}

Hard structural limits: ALL PASSED.
Assess contextual risk per policy thresholds. Output JSON with: approved, decision_type, risk_score, risk_reasoning, conditions."""

        response = self.call_llm(SYSTEM_PROMPT, user_msg)

        try:
            approved = bool(response.get("approved", False))
            risk_score = max(0.0, min(10.0, float(response.get("risk_score", 5.0))))
            risk_reasoning = str(response.get("risk_reasoning", "LLM assessment"))
            conditions = list(response.get("conditions", []))

            d_type_raw = str(response.get("decision_type", "APPROVED" if approved else "REJECTED_CONTEXTUAL")).upper()
            try:
                decision_type = RiskDecisionType(d_type_raw)
            except ValueError:
                decision_type = RiskDecisionType.APPROVED if approved else RiskDecisionType.REJECTED_CONTEXTUAL

            return RiskDecision(
                proposal_id=proposal.proposal_id,
                proposal_hash=proposal.proposal_hash,
                approved=approved,
                decision_type=decision_type,
                hard_rules_passed=True,
                conditions=conditions,
                risk_score=risk_score,
                risk_reasoning=risk_reasoning,
                expires_at=template.expires_at,
            )

        except Exception as exc:
            logger.error("RiskManager contextual parse failed: %s", exc)
            return self._fallback_decision(proposal, template)

    def _fallback_decision(self, proposal: TradeProposal, template: RiskDecision) -> RiskDecision:
        return RiskDecision(
            proposal_id=proposal.proposal_id,
            proposal_hash=proposal.proposal_hash,
            approved=False,
            decision_type=RiskDecisionType.REJECTED_CONTEXTUAL,
            hard_rules_passed=True,
            risk_score=8.0,
            risk_reasoning="[FALLBACK] LLM unavailable — defaulting to REJECTED for safety",
            expires_at=template.expires_at,
        )

    def _fallback(self, context: str) -> dict:
        return {
            "approved": False,
            "decision_type": "REJECTED_CONTEXTUAL",
            "risk_score": 8.0,
            "risk_reasoning": "[FALLBACK] LLM unavailable",
            "conditions": [],
        }
