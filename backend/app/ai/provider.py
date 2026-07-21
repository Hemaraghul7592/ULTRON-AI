from __future__ import annotations

import abc
import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ai.providers import GrokProvider as _NewGrokProvider
from app.ai.providers import OpenAIProvider as _NewOpenAIProvider
from app.core.config import get_settings
from app.core.exceptions import (
    AIServiceException,
    ProviderUnavailableException,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProvider(abc.ABC):
    def __init__(self, name: str, api_key: str, model: str) -> None:
        self.name = name
        self.api_key = api_key
        self.model = model
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

    @abc.abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        pass

    @abc.abstractmethod
    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass

    @abc.abstractmethod
    def get_models(self) -> list[str]:
        pass

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()

    def _parse_response(self, data: dict[str, Any]) -> dict[str, Any]:
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage = data.get("usage", {})
        tool_calls_raw = message.get("tool_calls", [])

        tool_calls = []
        for tc in tool_calls_raw:
            func = tc.get("function", {})
            try:
                args = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                args = {"raw": func.get("arguments", "")}
            tool_calls.append(
                {
                    "id": tc.get("id", ""),
                    "name": func.get("name", ""),
                    "arguments": args,
                }
            )

        return {
            "content": message.get("content", ""),
            "tool_calls": tool_calls,
            "finish_reason": choice.get("finish_reason", "stop"),
            "tokens_used": usage.get("total_tokens", 0),
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "model": data.get("model", self.model),
            "provider": self.name,
        }


class GroqProvider(AIProvider):
    BASE_URL = "https://api.groq.com/openai/v1"

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        super().__init__(name="groq", api_key=api_key, model=model)

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_models(self) -> list[str]:
        return [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview",
        ]

    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        start = time.monotonic()
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.monotonic() - start) * 1000
            result = self._parse_response(data)
            result["latency_ms"] = latency_ms
            logger.info(
                "groq_chat_complete",
                model=self.model,
                tokens=result["tokens_used"],
                latency_ms=latency_ms,
            )
            return result
        except httpx.HTTPStatusError as e:
            raise AIServiceException(
                provider=self.name,
                message=f"HTTP {e.response.status_code}: {e.response.text}",
            ) from e
        except httpx.RequestError as e:
            raise ProviderUnavailableException(
                provider=self.name,
                reason=str(e),
            ) from e

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        try:
            async with self.client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        yield {"content": "", "done": True, "finish_reason": "stop"}
                        return
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        tool_calls_raw = delta.get("tool_calls", [])
                        tool_calls = []
                        for tc in tool_calls_raw:
                            func = tc.get("function", {})
                            tool_calls.append(
                                {
                                    "id": tc.get("id", ""),
                                    "name": func.get("name", ""),
                                    "arguments": func.get("arguments", ""),
                                }
                            )
                        finish = data.get("choices", [{}])[0].get("finish_reason")
                        yield {
                            "content": content,
                            "done": finish is not None,
                            "tool_calls": tool_calls,
                            "finish_reason": finish,
                        }
                    except json.JSONDecodeError:
                        continue
        except httpx.RequestError as e:
            raise ProviderUnavailableException(
                provider=self.name,
                reason=str(e),
            ) from e


class GeminiProvider(AIProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        super().__init__(name="gemini", api_key=api_key, model=model)

    def is_available(self) -> bool:
        return bool(self.api_key)

    def get_models(self) -> list[str]:
        return [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.5-flash-8b",
        ]

    def _convert_messages(
        self,
        messages: list[dict[str, Any]],
    ) -> tuple[str, list[dict[str, Any]]]:
        system_instruction = ""
        contents = []
        for msg in messages:
            role = msg.get("role", "user")
            if role == "system":
                system_instruction = msg.get("content", "")
                continue
            gemini_role = "model" if role == "assistant" else "user"
            parts = [{"text": msg.get("content", "")}]
            contents.append({"role": gemini_role, "parts": parts})
        return system_instruction, contents

    def _convert_tools(self, tools: list[dict] | None) -> list[dict] | None:
        if not tools:
            return None
        function_declarations = []
        for tool in tools:
            func = tool.get("function", tool)
            function_declarations.append(
                {
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                }
            )
        return [{"function_declarations": function_declarations}]

    def _parse_gemini_response(self, data: dict[str, Any]) -> dict[str, Any]:
        candidates = data.get("candidates", [])
        if not candidates:
            return {
                "content": "",
                "tool_calls": [],
                "finish_reason": "stop",
                "tokens_used": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "model": self.model,
                "provider": self.name,
            }
        candidate = candidates[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        text_parts = []
        tool_calls = []
        for part in parts:
            if "text" in part:
                text_parts.append(part["text"])
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    {
                        "id": f"gemini_{fc.get('name', '')}",
                        "name": fc.get("name", ""),
                        "arguments": fc.get("args", {}),
                    }
                )
        usage = data.get("usageMetadata", {})
        return {
            "content": "\n".join(text_parts),
            "tool_calls": tool_calls,
            "finish_reason": candidate.get("finishReason", "STOP").lower(),
            "tokens_used": usage.get("totalTokenCount", 0),
            "prompt_tokens": usage.get("promptTokenCount", 0),
            "completion_tokens": usage.get("candidatesTokenCount", 0),
            "model": self.model,
            "provider": self.name,
        }

    async def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        system_instruction, contents = self._convert_messages(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        start = time.monotonic()
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/models/{self.model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            latency_ms = (time.monotonic() - start) * 1000
            result = self._parse_gemini_response(data)
            result["latency_ms"] = latency_ms
            return result
        except httpx.HTTPStatusError as e:
            raise AIServiceException(
                provider=self.name,
                message=f"HTTP {e.response.status_code}: {e.response.text}",
            ) from e
        except httpx.RequestError as e:
            raise ProviderUnavailableException(
                provider=self.name,
                reason=str(e),
            ) from e

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        system_instruction, contents = self._convert_messages(messages)
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        converted_tools = self._convert_tools(tools)
        if converted_tools:
            payload["tools"] = converted_tools

        try:
            async with self.client.stream(
                "POST",
                f"{self.BASE_URL}/models/{self.model}:streamGenerateContent?alt=sse",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self.api_key,
                },
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        result = self._parse_gemini_response(data)
                        yield {
                            "content": result["content"],
                            "done": False,
                            "tool_calls": result["tool_calls"],
                            "finish_reason": result["finish_reason"],
                        }
                    except json.JSONDecodeError:
                        continue
            yield {"content": "", "done": True, "finish_reason": "stop"}
        except httpx.RequestError as e:
            raise ProviderUnavailableException(
                provider=self.name,
                reason=str(e),
            ) from e


class AIProviderFactory:
    _providers: dict[str, type[AIProvider]] = {
        "groq": GroqProvider,
        "gemini": GeminiProvider,
        "openai": _NewOpenAIProvider,
        "grok": _NewGrokProvider,
    }

    @classmethod
    def create(cls, provider_name: str, api_key: str, model: str | None = None) -> AIProvider:
        provider_cls = cls._providers.get(provider_name)
        if not provider_cls:
            raise AIServiceException(
                provider=provider_name,
                message=f"Unknown provider: {provider_name}",
            )
        settings_obj = get_settings()
        if not model:
            model_map = {
                "groq": settings_obj.GROQ_MODEL,
                "gemini": settings_obj.GEMINI_MODEL,
                "openai": settings_obj.OPENAI_MODEL,
                "grok": settings_obj.GROK_MODEL,
            }
            model = model_map.get(provider_name, model)
        return provider_cls(api_key=api_key, model=model)

    @classmethod
    def register(cls, name: str, provider_cls: type[AIProvider]) -> None:
        cls._providers[name] = provider_cls

    @classmethod
    def available_providers(cls) -> list[str]:
        return list(cls._providers.keys())
