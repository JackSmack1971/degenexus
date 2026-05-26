"""Base agent: LLM client wrapper with structured output and deterministic fallback."""

from __future__ import annotations
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class AgentError(Exception):
    pass


class BaseAgent:
    """
    Wraps either Anthropic Claude or OpenRouter (OpenAI-compatible) for structured JSON output.
    Provider is selected via LLM_PROVIDER env var ("anthropic" default, "openrouter").
    Every subclass must implement `_fallback()` — a deterministic rule-based response
    used when the LLM API is unavailable.
    """

    MODEL = "claude-sonnet-4-6"  # used when LLM_PROVIDER=anthropic
    MAX_TOKENS = 2048
    MAX_RETRIES = 2

    def __init__(self, agent_id: str, performance_context: str = "") -> None:
        self.agent_id = agent_id
        self.performance_context = performance_context
        self._provider, self._client = self._init_client()

    def _init_client(self) -> tuple[str, Any]:
        """
        Returns (provider, client) where provider is one of:
          "anthropic" | "openrouter" | "fallback"
        and client is the corresponding SDK object (or None for fallback).
        """
        provider = os.getenv("LLM_PROVIDER", "anthropic").lower().strip()

        if provider == "openrouter":
            return self._init_openrouter()

        # Default: Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning(
                "%s: ANTHROPIC_API_KEY not set — will use deterministic fallback", self.agent_id
            )
            return "fallback", None
        try:
            import anthropic
            return "anthropic", anthropic.Anthropic(api_key=api_key)
        except ImportError:
            logger.error("anthropic package not installed")
            return "fallback", None

    def _init_openrouter(self) -> tuple[str, Any]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning(
                "%s: OPENROUTER_API_KEY not set — will use deterministic fallback", self.agent_id
            )
            return "fallback", None
        try:
            from src.core.openrouter_client import (
                OpenRouterClient,
                OpenRouterError,
                DEFAULT_MODEL,
            )
            model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
            client = OpenRouterClient(api_key=api_key, model=model)
            logger.info("%s: using OpenRouter model=%s", self.agent_id, client.model)
            return "openrouter", client
        except Exception as exc:
            logger.error(
                "%s: OpenRouter init failed: %s — using deterministic fallback",
                self.agent_id, exc,
            )
            return "fallback", None

    def _raw_llm_call(self, system_prompt: str, user_message: str) -> str:
        """Dispatch to the active provider and return raw response text. Raises on failure."""
        if self._provider == "anthropic":
            response = self._client.messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text.strip()

        if self._provider == "openrouter":
            return self._client.chat(
                system_prompt=system_prompt,
                user_message=user_message,
            )

        raise RuntimeError("No LLM client available")

    def call_llm(
        self,
        system_prompt: str,
        user_message: str,
    ) -> dict:
        """
        Call the LLM and return a parsed dict.
        Falls back to _fallback() on any failure.
        """
        if self._client is None:
            return self._fallback(user_message)

        full_system = self._inject_context(system_prompt)

        for attempt in range(self.MAX_RETRIES):
            try:
                raw = self._raw_llm_call(full_system, user_message)
                return self._parse_json(raw)

            except Exception as exc:
                logger.warning(
                    "%s LLM attempt %d/%d failed: %s",
                    self.agent_id, attempt + 1, self.MAX_RETRIES, exc
                )

        logger.error("%s: all LLM attempts failed, using fallback", self.agent_id)
        return self._fallback(user_message)

    def _inject_context(self, system_prompt: str) -> str:
        if not self.performance_context:
            return system_prompt
        return f"{system_prompt}\n\n{self.performance_context}"

    def _parse_json(self, raw: str) -> dict:
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        return json.loads(raw)

    def _fallback(self, context: str) -> dict:
        raise NotImplementedError(
            f"{self.agent_id} must implement _fallback() for LLM unavailability"
        )

    def update_context(self, context: str) -> None:
        self.performance_context = context
