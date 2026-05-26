"""Quant/Strategy Agent: signal → trade proposal with Kelly sizing."""

from __future__ import annotations
import logging
import math
from typing import Optional

from pydantic import ValidationError

from .base_agent import BaseAgent
from ..models.signals import MarketSignal, TradeProposal

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are the Quantitative Strategist at an AI trading firm.

Your job: given a market signal and portfolio state, design a precise trade proposal.

Requirements:
- Use Kelly Criterion at 0.5x fraction for position sizing (conservative half-Kelly).
  Kelly formula: f = (p*b - (1-p)) / b  where p=win_rate, b=avg_win/avg_loss
- Apply the 0.5x Kelly fraction to the available cash.
- entry_type: LIMIT unless confidence >= 0.85 AND entry zone is tight (< 0.2% from current price).
- stop_loss: below the invalidation_level (LONG) or above (SHORT).
- take_profit: must yield risk_reward_ratio >= 1.5.
- position_size_shares: must be integer >= 1.
- max_loss_usd = (entry_price - stop_loss) * shares for LONG.
- max_loss_pct = max_loss_usd / portfolio_value.
- portfolio_exposure_pct = (entry_price * shares) / portfolio_value.
- reasoning must show your Kelly calculation explicitly.

When no performance history is available (first session or new instrument):
- Default p = 0.55, b = 1.5 (conservative starting assumptions)
- Estimate avg_win ≈ 3% of entry price, avg_loss ≈ 1.5% of entry price
- Cap max loss per trade at 1% of portfolio value
- Cap position size at 15% of available cash to preserve dry powder
- These defaults are intentionally conservative; prefer empirical data when available.

If the Risk Capacity context shows current utilization is high (many open positions, high exposure),
reduce position size below Kelly to leave room for future opportunities.

Respond ONLY with valid JSON. No commentary."""


class QuantAgent(BaseAgent):

    def __init__(self, performance_context: str = "") -> None:
        super().__init__("QUANT", performance_context)

    def design_proposal(
        self,
        signal: MarketSignal,
        portfolio_value: float,
        available_cash: float,
        win_rate: float = 0.55,
        avg_win_usd: float = 0.0,
        avg_loss_usd: float = 0.0,
    ) -> Optional[TradeProposal]:
        try:
            user_msg = self._build_prompt(
                signal, portfolio_value, available_cash, win_rate, avg_win_usd, avg_loss_usd
            )
            response = self.call_llm(SYSTEM_PROMPT, user_msg)
            return self._parse_proposal(response, signal, portfolio_value)
        except Exception as exc:
            logger.error("QuantAgent failed: %s", exc)
            return self._fallback_proposal(signal, portfolio_value, available_cash)

    def _build_prompt(
        self,
        signal: MarketSignal,
        portfolio_value: float,
        available_cash: float,
        win_rate: float,
        avg_win_usd: float,
        avg_loss_usd: float,
    ) -> str:
        avg_win = avg_win_usd if avg_win_usd > 0 else signal.current_price * 0.03
        avg_loss = avg_loss_usd if avg_loss_usd > 0 else signal.current_price * 0.015
        safe_reasoning = self._sanitize_external_text(signal.reasoning)

        return f"""Design a trade proposal for this signal:

SIGNAL:
  {self.TRUST_BOUNDARY_NOTICE}
  Symbol: {signal.symbol}
  Direction: {signal.direction}
  Trend: {signal.trend.value}
  Confidence: {signal.confidence:.2f}
  Signal Strength: {signal.signal_strength.value}
  Current Price: ${signal.current_price:.4f}
  Entry Zone: ${signal.entry_zone.low:.4f} – ${signal.entry_zone.high:.4f}
  Invalidation Level: ${signal.invalidation_level:.4f}
  Reasoning: {safe_reasoning}

PORTFOLIO STATE:
  Portfolio Value: ${portfolio_value:,.2f}
  Available Cash: ${available_cash:,.2f}
  Historical Win Rate: {win_rate:.1%}
  Avg Win: ${avg_win:.2f}
  Avg Loss: ${avg_loss:.2f}

Kelly formula: f = (p*b - (1-p)) / b, half-Kelly = f/2
b = avg_win / avg_loss = {avg_win/avg_loss:.2f}
p = {win_rate:.2f}

Output JSON with fields:
entry_price, entry_type, stop_loss, take_profit,
position_size_shares, position_value_usd, max_loss_usd,
max_loss_pct, risk_reward_ratio, portfolio_exposure_pct,
time_in_force, expiry_bars, reasoning"""

    def _parse_proposal(
        self, response: dict, signal: MarketSignal, portfolio_value: float
    ) -> Optional[TradeProposal]:
        try:
            proposal = TradeProposal(
                signal_id=signal.signal_id,
                symbol=signal.symbol,
                direction=signal.direction,
                entry_type=str(response.get("entry_type", "LIMIT")).upper(),
                entry_price=float(response["entry_price"]),
                stop_loss=float(response["stop_loss"]),
                take_profit=float(response["take_profit"]),
                position_size_shares=int(response["position_size_shares"]),
                position_value_usd=float(response["position_value_usd"]),
                max_loss_usd=float(response["max_loss_usd"]),
                max_loss_pct=float(response["max_loss_pct"]),
                risk_reward_ratio=float(response["risk_reward_ratio"]),
                portfolio_exposure_pct=float(response["portfolio_exposure_pct"]),
                time_in_force=str(response.get("time_in_force", "GTC")),
                expiry_bars=int(response.get("expiry_bars", 12)),
                reasoning=str(response.get("reasoning", "")),
            )
            proposal.proposal_hash = proposal.compute_hash()
            return proposal
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            logger.error("Failed to parse quant response: %s — response: %s", exc, response)
            return None

    def _fallback_proposal(
        self,
        signal: MarketSignal,
        portfolio_value: float,
        available_cash: float,
    ) -> Optional[TradeProposal]:
        price = signal.current_price
        if price <= 0:
            return None

        risk_per_share = price * 0.015
        stop_loss = price - risk_per_share if signal.direction == "LONG" else price + risk_per_share
        take_profit = price + risk_per_share * 2.0 if signal.direction == "LONG" else price - risk_per_share * 2.0

        max_loss_budget = portfolio_value * 0.01
        shares = max(1, int(max_loss_budget / risk_per_share))
        shares = min(shares, int(available_cash * 0.15 / price))

        if shares <= 0:
            return None

        proposal = TradeProposal(
            signal_id=signal.signal_id,
            symbol=signal.symbol,
            direction=signal.direction,
            entry_type="LIMIT",
            entry_price=round(price, 4),
            stop_loss=round(stop_loss, 4),
            take_profit=round(take_profit, 4),
            position_size_shares=shares,
            position_value_usd=round(price * shares, 2),
            max_loss_usd=round(risk_per_share * shares, 2),
            max_loss_pct=round(risk_per_share * shares / portfolio_value, 4),
            risk_reward_ratio=2.0,
            portfolio_exposure_pct=round(price * shares / portfolio_value, 4),
            time_in_force="GTC",
            expiry_bars=12,
            reasoning="[FALLBACK] Conservative 1% risk, 2:1 R:R, 0.5x Kelly",
        )
        proposal.proposal_hash = proposal.compute_hash()
        return proposal

    def _fallback(self, context: str) -> dict:
        return {"entry_type": "LIMIT", "reasoning": "[FALLBACK] LLM unavailable"}
