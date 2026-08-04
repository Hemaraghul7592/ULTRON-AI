from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ai.providers.base import AIProvider
from app.core.exceptions import AIServiceException, ProviderUnavailableException
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(AIProvider):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        super().__init__(name="gemini", api_key=api_key, model=model)
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client

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
                },
            )
        return [{"function_declarations": function_declarations}]

    def _parse_gemini_response(self, data: dict[str, Any], latency_ms: float) -> dict[str, Any]:
        candidates = data.get("candidates", [])
        if not candidates:
            return self._empty_result(latency_ms)
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
                    },
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
            "latency_ms": latency_ms,
        }

    def _empty_result(self, latency_ms: float) -> dict[str, Any]:
        return {
            "content": "",
            "tool_calls": [],
            "finish_reason": "stop",
            "tokens_used": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "model": self.model,
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
            result = self._parse_gemini_response(data, latency_ms)
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
                        result = self._parse_gemini_response(data, 0)
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
            raise ProviderUnavailableException(provider=self.name, reason=str(e)) from e

    def _map_http_error(self, e: httpx.HTTPStatusError) -> AIServiceException:
        status = e.response.status_code
        body = e.response.text
        if status == 401 or status == 403:
            from app.core.exceptions import AIAuthenticationException

            return AIAuthenticationException(provider=self.name, message=body)
        if status == 429:
            from app.core.exceptions import AIRateLimitException

            return AIRateLimitException(provider=self.name, message=body)
        return AIServiceException(
            provider=self.name,
            message=f"HTTP {status}: {body}",
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
