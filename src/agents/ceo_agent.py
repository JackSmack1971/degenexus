"""CEO Agent: signal triage, debate arbitration, and final trade decisions."""

from __future__ import annotations
import logging

from .base_agent import BaseAgent
from ..models.signals import MarketSignal, TradeProposal, RiskDecision

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the CEO of an AI trading firm.
Your role: triage analyst signals, guide the debate, issue final trade decisions.

Rules:
- You may challenge the analyst if their signal direction contradicts the indicators.
- You may challenge the quant if their position sizing seems too aggressive.
- You cannot override the Risk Manager's veto — it is system-enforced.
- You may issue one counter-challenge to Risk Manager per trade cycle.
- Final decision: PROCEED or ABORT with reasoning.
- Any signal with data_quality SYNTHETIC or STALE: ABORT immediately.

Signal quality guidance (for triage decisions):
- Confidence >= 0.70: strong signal — proceed unless clear red flags.
- Confidence 0.50–0.70: moderate signal — scrutinize for conflicting indicators, weak reasoning, or unfavourable market context. Proceed with conviction only.
- Confidence < 0.50: weak signal — ABORT unless the setup is truly exceptional. Fallback or LLM-unavailable signals should always be ABORTed.
- Any signal with "[FALLBACK]" in reasoning: ABORT immediately.

Counter-challenge guidance:
- Only challenge contextual rejections (hard rule violations are not challengeable).
- Weigh opportunity cost against risk: high confidence (>= 0.75) and strong R:R (>= 2.0)
  are meaningful signals worth examining. But defer to risk manager on borderline calls.
- Be skeptical of your own optimism — the risk manager has context you may lack.

Respond with JSON: {"decision": "PROCEED" or "ABORT", "reasoning": "..."}"""


class CEOAgent(BaseAgent):

    def __init__(self, performance_context: str = "") -> None:
        super().__init__("CEO", performance_context)

    def triage_signal(
        self,
        signal: MarketSignal,
        open_positions_count: int,
    ) -> str:
        """Evaluate signal quality. Returns 'PROCEED' or 'ABORT'."""
        user_msg = f"""Triage this analyst signal:

SIGNAL:
  Symbol: {signal.symbol}
  Direction: {signal.direction}
  Trend: {signal.trend.value}
  Data Quality: {signal.data_quality.value}
  Confidence: {signal.confidence:.2f}
  Signal Strength: {signal.signal_strength.value}
  Reasoning: {signal.reasoning}
  Market Context: {signal.market_context}

PORTFOLIO STATE:
  Open Positions: {open_positions_count}

Should we proceed to the quant design phase?
Output JSON: {{"decision": "PROCEED" or "ABORT", "reasoning": "..."}}"""

        response = self.call_llm(SYSTEM_PROMPT, user_msg)
        decision = str(response.get("decision", "ABORT")).upper()
        return "PROCEED" if decision == "PROCEED" else "ABORT"

    def decide_counter_challenge(
        self,
        signal: MarketSignal,
        proposal: TradeProposal,
        risk_decision: RiskDecision,
    ) -> bool:
        """
        Decide whether to counter-challenge a contextual risk rejection.
        Hard rule violations are never challengeable — caller must enforce this.
        Returns True to issue counter-challenge.
        """
        user_msg = f"""The Risk Manager has rejected a trade. Should you issue a counter-challenge?

SIGNAL:
  Symbol: {signal.symbol}
  Confidence: {signal.confidence:.2f}
  Reasoning: {signal.reasoning}

PROPOSAL:
  Direction: {proposal.direction}
  R:R Ratio: {proposal.risk_reward_ratio:.2f}
  Max Loss: ${proposal.max_loss_usd:.2f} ({proposal.max_loss_pct:.2%})

RISK REJECTION:
  Risk Score: {risk_decision.risk_score:.1f}/10
  Reasoning: {risk_decision.risk_reasoning}

Output JSON: {{"decision": "CHALLENGE" or "ACCEPT", "reasoning": "..."}}"""

        response = self.call_llm(SYSTEM_PROMPT, user_msg)
        decision = str(response.get("decision", "ACCEPT")).upper()
        return decision == "CHALLENGE"

    def _fallback(self, context: str) -> dict:
        return {
            "decision": "ABORT",
            "reasoning": "[FALLBACK] LLM unavailable — defaulting to ABORT",
        }
