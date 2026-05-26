"""Tests for CEO signal triage prompt contents."""

from src.agents.ceo_agent import CEOAgent
from src.models.signals import DataQuality


def test_triage_prompt_includes_data_quality(valid_signal):
    agent = CEOAgent()
    valid_signal.data_quality = DataQuality.STALE
    captured = {}

    def fake_call_llm(system_prompt: str, user_message: str) -> dict:
        captured["system_prompt"] = system_prompt
        captured["user_message"] = user_message
        return {"decision": "ABORT", "reasoning": "stale data"}

    agent.call_llm = fake_call_llm

    decision = agent.triage_signal(valid_signal, open_positions_count=1)

    assert decision == "ABORT"
    assert "data_quality SYNTHETIC or STALE" in captured["system_prompt"]
    assert "Data Quality: STALE" in captured["user_message"]
