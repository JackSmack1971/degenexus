"""Tests for OpenRouter client — allowlist enforcement and integration plumbing."""

import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.openrouter_client import (
    ALLOWED_FREE_MODELS,
    DEFAULT_MODEL,
    OpenRouterClient,
    OpenRouterError,
    validate_model,
)


# ---------------------------------------------------------------------------
# validate_model
# ---------------------------------------------------------------------------

class TestValidateModel:
    def test_allowed_model_passes(self):
        result = validate_model("meta-llama/llama-3.3-70b-instruct")
        assert result == "meta-llama/llama-3.3-70b-instruct"

    def test_every_listed_model_passes(self):
        for model in ALLOWED_FREE_MODELS:
            assert validate_model(model) == model

    def test_unknown_model_raises(self):
        with pytest.raises(OpenRouterError, match="not in the approved free-model allowlist"):
            validate_model("openai/gpt-4o")

    def test_paid_anthropic_model_raises(self):
        with pytest.raises(OpenRouterError):
            validate_model("anthropic/claude-opus-4")

    def test_empty_string_raises(self):
        with pytest.raises(OpenRouterError):
            validate_model("")

    def test_allowlist_is_frozenset(self):
        # Verify the allowlist cannot be mutated at runtime
        assert isinstance(ALLOWED_FREE_MODELS, frozenset)

    def test_default_model_is_in_allowlist(self):
        assert DEFAULT_MODEL in ALLOWED_FREE_MODELS

    def test_allowlist_has_17_models(self):
        assert len(ALLOWED_FREE_MODELS) == 17


# ---------------------------------------------------------------------------
# OpenRouterClient construction
# ---------------------------------------------------------------------------

class TestOpenRouterClientConstruction:
    def _make_client(self, model=DEFAULT_MODEL, api_key="sk-or-test"):
        with patch("src.core.openrouter_client.OpenAI") as mock_openai_cls:
            client = OpenRouterClient(api_key=api_key, model=model)
            mock_openai_cls.assert_called_once()
            return client, mock_openai_cls

    def test_valid_model_constructs(self):
        client, _ = self._make_client("meta-llama/llama-3.3-70b-instruct")
        assert client.model == "meta-llama/llama-3.3-70b-instruct"

    def test_invalid_model_raises_before_openai_init(self):
        with pytest.raises(OpenRouterError, match="not in the approved free-model allowlist"):
            OpenRouterClient(api_key="sk-or-test", model="openai/gpt-4o")

    def test_missing_openai_package_raises(self):
        with patch("src.core.openrouter_client.OpenAI", None):
            with pytest.raises(OpenRouterError, match="openai package not installed"):
                OpenRouterClient(api_key="sk-or-test", model=DEFAULT_MODEL)

    def test_base_url_is_openrouter(self):
        with patch("src.core.openrouter_client.OpenAI") as mock_openai_cls:
            OpenRouterClient(api_key="sk-or-test", model=DEFAULT_MODEL)
            call_kwargs = mock_openai_cls.call_args.kwargs
            assert call_kwargs["base_url"] == "https://openrouter.ai/api/v1"

    def test_api_key_passed_to_openai(self):
        with patch("src.core.openrouter_client.OpenAI") as mock_openai_cls:
            OpenRouterClient(api_key="sk-or-secret", model=DEFAULT_MODEL)
            call_kwargs = mock_openai_cls.call_args.kwargs
            assert call_kwargs["api_key"] == "sk-or-secret"

    def test_timeout_passed_to_openai(self):
        with patch("src.core.openrouter_client.OpenAI") as mock_openai_cls:
            OpenRouterClient(api_key="sk-or-secret", model=DEFAULT_MODEL, timeout=12.5)
            call_kwargs = mock_openai_cls.call_args.kwargs
            assert call_kwargs["timeout"] == 12.5


# ---------------------------------------------------------------------------
# OpenRouterClient.chat()
# ---------------------------------------------------------------------------

class TestOpenRouterClientChat:
    def _make_client_with_mock_response(self, content: str):
        mock_message = MagicMock()
        mock_message.content = content
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        with patch("src.core.openrouter_client.OpenAI") as mock_openai_cls:
            mock_openai_instance = mock_openai_cls.return_value
            mock_openai_instance.chat.completions.create.return_value = mock_response
            client = OpenRouterClient(api_key="sk-or-test", model=DEFAULT_MODEL)
        # client._client is the mock instance; patch is exited but mock_openai_instance still works
        return client, mock_openai_instance

    def test_chat_returns_response_text(self):
        client, mock_instance = self._make_client_with_mock_response('{"signal": "LONG"}')
        result = client.chat(system_prompt="You are a trader", user_message="Analyse AAPL")
        assert result == '{"signal": "LONG"}'

    def test_chat_passes_system_and_user_as_messages(self):
        client, mock_instance = self._make_client_with_mock_response("ok")
        client.chat(system_prompt="sys", user_message="usr")
        call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "sys"}
        assert messages[1] == {"role": "user", "content": "usr"}

    def test_chat_passes_model_id(self):
        client, mock_instance = self._make_client_with_mock_response("ok")
        client.chat(system_prompt="sys", user_message="usr")
        call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == DEFAULT_MODEL

    def test_chat_sends_title_header(self):
        client, mock_instance = self._make_client_with_mock_response("ok")
        client.chat(system_prompt="sys", user_message="usr")
        call_kwargs = mock_instance.chat.completions.create.call_args.kwargs
        headers = call_kwargs.get("extra_headers", {})
        assert "X-OpenRouter-Title" in headers

    def test_chat_returns_empty_string_for_none_content(self):
        client, mock_instance = self._make_client_with_mock_response(None)
        result = client.chat(system_prompt="sys", user_message="usr")
        assert result == ""


# ---------------------------------------------------------------------------
# BaseAgent provider switching
# ---------------------------------------------------------------------------

class TestBaseAgentProviderSwitching:
    def test_openrouter_provider_selected_via_env(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        monkeypatch.setenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "12.5")

        import src.core.openrouter_client as or_mod
        import src.agents.base_agent as ba_mod

        with patch.object(or_mod, "OpenAI") as mock_openai_cls:
            # Force re-init by instantiating a fresh agent class
            class DummyAgent(ba_mod.BaseAgent):
                def _fallback(self, context):
                    return {}

            agent = DummyAgent(agent_id="TEST")
            assert agent._provider == "openrouter"
            assert agent._llm_timeout_seconds == 12.5
            assert mock_openai_cls.call_args.kwargs["timeout"] == 12.5

    def test_anthropic_provider_is_default(self, monkeypatch):
        pytest.importorskip("anthropic")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("LLM_TIMEOUT_SECONDS", "9")

        with patch("anthropic.Anthropic") as mock_anthropic:
            from src.agents.base_agent import BaseAgent

            class DummyAgent(BaseAgent):
                def _fallback(self, context):
                    return {}

            agent = DummyAgent(agent_id="TEST")
            assert agent._provider == "anthropic"
            assert agent._llm_timeout_seconds == 9.0
            assert mock_anthropic.call_args.kwargs["timeout"] == 9.0

    def test_missing_openrouter_key_falls_back(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        from src.agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            def _fallback(self, context):
                return {"fallback": True}

        agent = DummyAgent(agent_id="TEST")
        assert agent._provider == "fallback"
        assert agent._client is None

    def test_timeout_error_retries_then_falls_back(self, monkeypatch, caplog):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        monkeypatch.setenv("OPENROUTER_MODEL", DEFAULT_MODEL)
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")

        from src.agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            def _fallback(self, context):
                return {"fallback": True}

        with patch("src.core.openrouter_client.OpenAI"):
            agent = DummyAgent(agent_id="TEST")
        agent._raw_llm_call = MagicMock(side_effect=TimeoutError("request timed out"))

        with caplog.at_level(logging.WARNING):
            response = agent.call_llm("sys", "user")

        assert response == {"fallback": True}
        assert agent._raw_llm_call.call_count == agent.MAX_RETRIES
        assert "request timed out" in caplog.text

    def test_invalid_openrouter_model_falls_back(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o")  # not in allowlist

        from src.agents.base_agent import BaseAgent

        class DummyAgent(BaseAgent):
            def _fallback(self, context):
                return {"fallback": True}

        agent = DummyAgent(agent_id="TEST")
        assert agent._provider == "fallback"
        assert agent._client is None
