from __future__ import annotations

import time
from collections.abc import AsyncIterator  # noqa: TC003
from typing import Any

from app.ai.providers import AIProvider, GeminiProvider, GrokProvider, GroqProvider, OpenAIProvider
from app.core.config import get_settings
from app.core.exceptions import AIServiceException, ProviderUnavailableException
from app.core.logging import get_logger

settings = get_settings()

logger = get_logger(__name__)


class AIService:
    """Single entry point for all AI provider interactions.

    Manages provider lifecycle, selection, fallback, and metrics.
    """

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._init_providers()

    def _init_providers(self) -> None:
        if settings.GROQ_API_KEY:
            self._providers["groq"] = GroqProvider(api_key=settings.GROQ_API_KEY)
        if settings.GEMINI_API_KEY:
            self._providers["gemini"] = GeminiProvider(api_key=settings.GEMINI_API_KEY)
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = OpenAIProvider(
                api_key=settings.OPENAI_API_KEY.get_secret_value(),
            )
        if settings.GROK_API_KEY:
            self._providers["grok"] = GrokProvider(api_key=settings.GROK_API_KEY.get_secret_value())

        logger.info(
            "ai_providers_initialized",
            available=list(self._providers.keys()),
        )

    @property
    def providers(self) -> dict[str, AIProvider]:
        return dict(self._providers)

    def get_provider(self, name: str) -> AIProvider | None:
        return self._providers.get(name)

    def get_available_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "model": p.model,
                "available": p.is_available(),
                "models": p.get_models(),
            }
            for p in self._providers.values()
            if p.is_available()
        ]

    async def chat(
        self,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        fallback: list[str] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        providers_to_try: list[str] = []
        if provider:
            if provider in self._providers:
                providers_to_try.append(provider)
            else:
                raise ProviderUnavailableException(
                    provider=provider,
                    reason="Provider not configured",
                )
        elif fallback:
            providers_to_try = [p for p in fallback if p in self._providers]
        else:
            providers_to_try = list(self._providers.keys())

        last_error: Exception | None = None
        for p_name in providers_to_try:
            p = self._providers.get(p_name)
            if not p or not p.is_available():
                continue
            try:
                return await p.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )
            except AIServiceException as e:
                logger.warning(
                    "provider_fallback",
                    provider=p_name,
                    error=str(e),
                )
                last_error = e
                continue

        raise last_error or ProviderUnavailableException(
            provider=provider or "all",
            reason="No available providers",
        )

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        provider: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        p = self._providers.get(provider)
        if not p:
            raise ProviderUnavailableException(
                provider=provider,
                reason="Provider not configured",
            )

        start = time.monotonic()
        async for chunk in p.chat_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            **kwargs,
        ):
            yield chunk

        latency = (time.monotonic() - start) * 1000
        logger.info(
            "stream_complete",
            provider=provider,
            model=p.model,
            latency_ms=latency,
        )

    async def close(self) -> None:
        for p in self._providers.values():
            await p.close()
        self._providers.clear()


ai_service = AIService()
