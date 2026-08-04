from __future__ import annotations

from collections.abc import AsyncIterator  # noqa: TC003
from typing import Any

from app.ai.provider import AIProvider, AIProviderFactory
from app.core.config import get_settings
from app.core.exceptions import ProviderUnavailableException
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProviderRouter:
    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._fallback_order: list[str] = []
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        settings_obj = get_settings()
        provider_configs = [
            ("groq", settings_obj.GROQ_API_KEY),
            ("gemini", settings_obj.GEMINI_API_KEY),
            (
                "openai",
                settings_obj.OPENAI_API_KEY.get_secret_value()
                if settings_obj.OPENAI_API_KEY
                else "",
            ),
            (
                "grok",
                settings_obj.GROK_API_KEY.get_secret_value() if settings_obj.GROK_API_KEY else "",
            ),
        ]
        for name, api_key in provider_configs:
            if api_key:
                try:
                    provider = AIProviderFactory.create(name, api_key)
                    self._providers[name] = provider
                    self._fallback_order.append(name)
                except Exception as e:
                    logger.error(f"failed_to_init_{name}", error=str(e))

        logger.info(
            "ai_router_initialized",
            providers=list(self._providers.keys()),
            fallback_order=self._fallback_order,
        )

    def get_provider(self, name: str | None = None) -> AIProvider:
        if name and name in self._providers:
            return self._providers[name]
        if name:
            raise ProviderUnavailableException(provider=name, reason="Provider not configured")

        settings_obj = get_settings()
        default = settings_obj.DEFAULT_AI_PROVIDER
        if default in self._providers:
            return self._providers[default]

        for provider_name in self._fallback_order:
            if provider_name in self._providers:
                return self._providers[provider_name]

        raise ProviderUnavailableException(provider="all", reason="No AI providers available")

    async def chat(
        self,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        primary = self.get_provider(provider)
        tried = set()
        current = primary

        while True:
            try:
                result = await current.chat(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                )
                return result
            except Exception as e:
                tried.add(current.name)
                logger.warning(
                    "provider_failed",
                    provider=current.name,
                    error=str(e),
                )
                next_provider = self._get_next_provider(tried)
                if next_provider is None:
                    raise
                current = next_provider

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        primary = self.get_provider(provider)
        tried = set()
        current = primary

        while True:
            try:
                async for chunk in current.chat_stream(
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    tools=tools,
                    **kwargs,
                ):
                    yield chunk
                return
            except Exception as e:
                tried.add(current.name)
                logger.warning("provider_stream_failed", provider=current.name, error=str(e))
                next_provider = self._get_next_provider(tried)
                if next_provider is None:
                    raise
                current = next_provider

    def _get_next_provider(self, tried: set[str]) -> AIProvider | None:
        for name in self._fallback_order:
            if name not in tried and name in self._providers:
                return self._providers[name]
        return None

    def get_available_providers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": name,
                "available": provider.is_available(),
                "models": provider.get_models(),
                "default_model": provider.model,
            }
            for name, provider in self._providers.items()
        ]

    async def close(self) -> None:
        for provider in self._providers.values():
            await provider.close()
