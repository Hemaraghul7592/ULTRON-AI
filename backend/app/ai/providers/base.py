from __future__ import annotations

import abc
from collections.abc import AsyncIterator  # noqa: TC003
from typing import Any


class AIProvider(abc.ABC):
    def __init__(self, name: str, api_key: str, model: str) -> None:
        self.name = name
        self.api_key = api_key
        self.model = model

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]: ...

    @abc.abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]: ...

    @abc.abstractmethod
    def is_available(self) -> bool: ...

    @abc.abstractmethod
    def get_models(self) -> list[str]: ...

    @abc.abstractmethod
    async def close(self) -> None:
        pass
