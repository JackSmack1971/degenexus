"""OpenRouter LLM client — enforces the approved free-model allowlist."""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[assignment,misc]

ALLOWED_FREE_MODELS: frozenset[str] = frozenset({
    "openrouter/owl-alpha",
    "deepseek/deepseek-v4-flash-20260423",
    "google/gemma-4-26b-a4b-it-20260403",
    "google/gemma-4-31b-it-20260402",
    "arcee-ai/trinity-large-thinking",
    "nvidia/nemotron-3-super-120b-a12b-20230311",
    "minimax/minimax-m2.5-20260211",
    "nvidia/nemotron-3-nano-30b-a3b",
    "qwen/qwen3-next-80b-a3b-instruct-2509",
    "nvidia/nemotron-nano-9b-v2",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "z-ai/glm-4.5-air",
    "qwen/qwen3-coder-480b-a35b-07-25",
    "meta-llama/llama-3.3-70b-instruct",
    "meta-llama/llama-3.2-3b-instruct",
    "nousresearch/hermes-3-llama-3.1-405b",
})

DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterError(Exception):
    pass


def validate_model(model_id: str) -> str:
    """Raise OpenRouterError if model_id is not in the approved allowlist."""
    if model_id not in ALLOWED_FREE_MODELS:
        raise OpenRouterError(
            f"Model '{model_id}' is not in the approved free-model allowlist.\n"
            f"Allowed models: {sorted(ALLOWED_FREE_MODELS)}"
        )
    return model_id


class OpenRouterClient:
    """
    Thin wrapper around the OpenAI SDK pointed at OpenRouter.
    Validates model against ALLOWED_FREE_MODELS on construction.
    Provides chat(system_prompt, user_message) -> str interface
    identical to the Anthropic path in BaseAgent.
    """

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0,
    ) -> None:
        self.model = validate_model(model)
        self.timeout = timeout
        if OpenAI is None:
            raise OpenRouterError(
                "openai package not installed — run: pip install openai>=1.0.0"
            )
        self._client = OpenAI(
            base_url=_OPENROUTER_BASE_URL,
            api_key=api_key,
            timeout=timeout,
        )
        logger.info("OpenRouterClient initialised: model=%s", self.model)

    def chat(self, system_prompt: str, user_message: str) -> str:
        """Send a chat message and return the response text."""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            extra_headers={"X-OpenRouter-Title": "AI-Trading-Company"},
        )
        return response.choices[0].message.content or ""
