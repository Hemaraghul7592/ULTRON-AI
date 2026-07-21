from __future__ import annotations

import json
import time
from typing import Any, AsyncIterator

import httpx

from app.ai.providers.base import AIProvider
from app.core.exceptions import AIServiceException, ProviderUnavailableException
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAICompatibleProvider(AIProvider):
    """Base for all OpenAI-compatible API providers (OpenAI, Groq, Grok, etc.)."""

    BASE_URL: str = ""

    def __init__(self, name: str, api_key: str, model: str) -> None:
        super().__init__(name=name, api_key=api_key, model=model)
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_chat_payload(
        self,
        messages: list[dict[str, Any]],
        temperature: float,
        max_tokens: int,
        tools: list[dict] | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
            payload["stream_options"] = {"include_usage": True}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    def _parse_response(self, data: dict[str, Any], latency_ms: float) -> dict[str, Any]:
        choices = data.get("choices", [])
        choice = choices[0] if choices else {}
        message = choice.get("message", {})
        usage = data.get("usage", {})

        tool_calls = []
        for tc in message.get("tool_calls", []):
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {"raw": func.get("arguments", "")}
            tool_calls.append({
                "id": tc.get("id", ""),
                "name": func.get("name", ""),
                "arguments": args,
            })

        return {
            "content": message.get("content", ""),
            "tool_calls": tool_calls,
            "finish_reason": choice.get("finish_reason", "stop"),
            "tokens_used": usage.get("total_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "model": data.get("model", self.model),
            "provider": self.name,
            "latency_ms": latency_ms,
        }

    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = self._build_chat_payload(messages, temperature, max_tokens, tools)
        start = time.monotonic()
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.monotonic() - start) * 1000
            result = self._parse_response(data, latency_ms)
            logger.info(
                "provider_chat_complete",
                provider=self.name,
                model=self.model,
                tokens=result["tokens_used"],
                latency_ms=latency_ms,
            )
            return result
        except httpx.HTTPStatusError as e:
            raise self._map_http_error(e)
        except httpx.RequestError as e:
            raise ProviderUnavailableException(provider=self.name, reason=str(e)) from e

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        payload = self._build_chat_payload(messages, temperature, max_tokens, tools, stream=True)
        try:
            async with self.client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._build_headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        yield {"content": "", "done": True, "finish_reason": "stop"}
                        return
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})
                        content = delta.get("content", "")
                        finish = choices[0].get("finish_reason")
                        tool_calls = []
                        for tc in delta.get("tool_calls", []):
                            func = tc.get("function", {})
                            tool_calls.append({
                                "id": tc.get("id", ""),
                                "name": func.get("name", ""),
                                "arguments": func.get("arguments", ""),
                            })
                        yield {
                            "content": content,
                            "done": finish is not None,
                            "tool_calls": tool_calls,
                            "finish_reason": finish,
                        }
                    except json.JSONDecodeError:
                        continue
        except httpx.RequestError as e:
            raise ProviderUnavailableException(provider=self.name, reason=str(e)) from e

    def _map_http_error(self, e: httpx.HTTPStatusError) -> AIServiceException:
        status = e.response.status_code
        body = e.response.text
        if status == 401:
            from app.core.exceptions import AIAuthenticationException
            return AIAuthenticationException(provider=self.name, message=body)
        if status == 429:
            from app.core.exceptions import AIRateLimitException
            return AIRateLimitException(provider=self.name, message=body)
        if status == 400 and "context_length" in body.lower():
            from app.core.exceptions import AIContextLengthException
            return AIContextLengthException(provider=self.name, message=body)
        return AIServiceException(
            provider=self.name,
            message=f"HTTP {status}: {body}",
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
