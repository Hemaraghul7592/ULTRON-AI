from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.ai.providers import GeminiProvider, GrokProvider, GroqProvider, OpenAIProvider
from app.ai.service import AIService
from app.core.exceptions import (
    AIAuthenticationException,
    AIContextLengthException,
    AIRateLimitException,
    AIServiceException,
    ProviderUnavailableException,
)


class TestAIExceptions:
    def test_ai_authentication_exception(self):
        exc = AIAuthenticationException(provider="openai", message="Invalid key")
        assert exc.code == "AI_AUTHENTICATION_ERROR"
        assert "openai" in str(exc)
        assert "Invalid key" in str(exc)

    def test_ai_rate_limit_exception(self):
        exc = AIRateLimitException(provider="groq", message="Too fast")
        assert exc.code == "AI_RATE_LIMIT"
        assert "Too fast" in str(exc)

    def test_ai_context_length_exception(self):
        exc = AIContextLengthException(provider="gemini", message="Too long")
        assert exc.code == "AI_CONTEXT_LENGTH"
        assert "Too long" in str(exc)


def _make_response(status_code: int, json_data: dict | None = None) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.text = str(json_data) if json_data else ""
    if json_data is not None:
        resp.json = MagicMock(return_value=json_data)
    resp.raise_for_status = MagicMock()
    return resp


def _make_stream_response(lines: list[str]) -> MagicMock:
    async def aiter_lines():
        for line in lines:
            yield line

    resp = MagicMock(spec=httpx.Response)
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.aiter_lines = aiter_lines
    return resp


class TestOpenAICompatibleProvider:
    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key", model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_is_available_with_key(self, provider):
        assert provider.is_available()

    @pytest.mark.asyncio
    async def test_is_available_no_key(self):
        p = OpenAIProvider(api_key="", model="gpt-4o-mini")
        assert not p.is_available()

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Hello from AI", "tool_calls": []},
                    "finish_reason": "stop",
                },
            ],
            "usage": {"total_tokens": 10, "prompt_tokens": 5, "completion_tokens": 5},
            "model": "gpt-4o-mini",
        }
        resp = _make_response(200, mock_response)
        provider._client = MagicMock()
        provider._client.post = AsyncMock(return_value=resp)

        result = await provider.chat(messages=[{"role": "user", "content": "Hi"}])

        assert result["content"] == "Hello from AI"
        assert result["finish_reason"] == "stop"
        assert result["tokens_used"] == 10
        assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_chat_http_401(self, provider):
        mock_resp = _make_response(401)
        mock_resp.text = "Invalid API key"
        provider._client = MagicMock()
        provider._client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401",
                request=MagicMock(),
                response=mock_resp,
            ),
        )

        with pytest.raises(AIAuthenticationException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_http_429(self, provider):
        mock_resp = _make_response(429)
        mock_resp.text = "Rate limited"
        provider._client = MagicMock()
        provider._client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "429",
                request=MagicMock(),
                response=mock_resp,
            ),
        )

        with pytest.raises(AIRateLimitException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_context_length(self, provider):
        mock_resp = _make_response(400)
        mock_resp.text = "context_length_exceeded"
        provider._client = MagicMock()
        provider._client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "400",
                request=MagicMock(),
                response=mock_resp,
            ),
        )

        with pytest.raises(AIContextLengthException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_request_error(self, provider):
        provider._client = MagicMock()
        provider._client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

        with pytest.raises(ProviderUnavailableException) as exc:
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        assert "Connection failed" in str(exc.value)

    @pytest.mark.asyncio
    async def test_chat_stream_yields_chunks(self, provider):
        lines = [
            'data: {"choices":[{"delta":{"content":"Hello"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{"content":" world"},"finish_reason":null}]}',
            'data: {"choices":[{"delta":{}},"finish_reason":"stop"}]}',
            "data: [DONE]",
        ]
        stream_resp = _make_stream_response(lines)

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=stream_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        provider._client = MagicMock()
        provider._client.stream = MagicMock(return_value=mock_ctx)

        chunks = []
        async for chunk in provider.chat_stream(messages=[{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[0]["content"] == "Hello"
        assert chunks[-1]["done"] is True


class TestOpenAIProvider:
    def test_base_url(self):
        p = OpenAIProvider(api_key="test")
        assert p.BASE_URL == "https://api.openai.com/v1"

    def test_models(self):
        p = OpenAIProvider(api_key="test")
        assert "gpt-4o" in p.get_models()
        assert "gpt-4o-mini" in p.get_models()


class TestGroqProvider:
    def test_base_url(self):
        p = GroqProvider(api_key="test")
        assert p.BASE_URL == "https://api.groq.com/openai/v1"

    def test_models(self):
        p = GroqProvider(api_key="test")
        assert "llama-3.3-70b-versatile" in p.get_models()


class TestGrokProvider:
    def test_base_url(self):
        p = GrokProvider(api_key="test")
        assert p.BASE_URL == "https://api.x.ai/v1"

    def test_models(self):
        p = GrokProvider(api_key="test")
        assert "grok-2-latest" in p.get_models()


class TestGeminiProvider:
    @pytest.fixture
    def provider(self):
        return GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

    @pytest.mark.asyncio
    async def test_chat_success(self, provider):
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Hello from Gemini"}],
                    },
                    "finishReason": "STOP",
                },
            ],
            "usageMetadata": {
                "totalTokenCount": 10,
                "promptTokenCount": 5,
                "candidatesTokenCount": 5,
            },
        }
        resp = _make_response(200, mock_response)
        provider._client = MagicMock()
        provider._client.post = AsyncMock(return_value=resp)

        result = await provider.chat(messages=[{"role": "user", "content": "Hi"}])

        assert result["content"] == "Hello from Gemini"
        assert result["finish_reason"] == "stop"
        assert result["provider"] == "gemini"

    def test_convert_messages_with_system(self, provider):
        system, contents = provider._convert_messages(
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ],
        )
        assert system == "You are helpful"
        assert len(contents) == 1

    @pytest.mark.asyncio
    async def test_no_candidates(self, provider):
        resp = _make_response(200, {"candidates": []})
        provider._client = MagicMock()
        provider._client.post = AsyncMock(return_value=resp)

        result = await provider.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result["content"] == ""

    @pytest.mark.asyncio
    async def test_chat_http_401(self, provider):
        mock_resp = _make_response(401)
        mock_resp.text = "Unauthorized"
        provider._client = MagicMock()
        provider._client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401",
                request=MagicMock(),
                response=mock_resp,
            ),
        )

        with pytest.raises(AIAuthenticationException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_http_429(self, provider):
        mock_resp = _make_response(429)
        mock_resp.text = "Rate limited"
        provider._client = MagicMock()
        provider._client.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "429",
                request=MagicMock(),
                response=mock_resp,
            ),
        )

        with pytest.raises(AIRateLimitException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_request_error(self, provider):
        provider._client = MagicMock()
        provider._client.post = AsyncMock(side_effect=httpx.RequestError("Connection failed"))

        with pytest.raises(ProviderUnavailableException):
            await provider.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_stream(self, provider):
        lines = [
            'data: {"candidates":[{"content":{"parts":[{"text":"Hello"}]},"finishReason":"STOP"}]}',
        ]
        stream_resp = _make_stream_response(lines)

        mock_ctx = MagicMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=stream_resp)
        mock_ctx.__aexit__ = AsyncMock(return_value=None)

        provider._client = MagicMock()
        provider._client.stream = MagicMock(return_value=mock_ctx)

        chunks = []
        async for chunk in provider.chat_stream(messages=[{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 2
        assert chunks[0]["content"] == "Hello"
        assert chunks[-1]["done"] is True


class TestAIService:
    @pytest.fixture
    def mock_provider(self):
        provider = MagicMock()
        provider.name = "test"
        provider.model = "test-model"
        provider.is_available.return_value = True
        provider.get_models.return_value = ["test-model"]
        provider.chat = AsyncMock(return_value={"content": "test", "finish_reason": "stop"})
        return provider

    @pytest.mark.asyncio
    async def test_get_provider(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        assert service.get_provider("test") is mock_provider
        assert service.get_provider("nonexistent") is None

    @pytest.mark.asyncio
    async def test_chat_with_provider(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        result = await service.chat(messages=[{"role": "user", "content": "Hi"}], provider="test")
        assert result["content"] == "test"

    @pytest.mark.asyncio
    async def test_chat_fallback(self, mock_provider):
        failing = MagicMock()
        failing.name = "failing"
        failing.is_available.return_value = True
        failing.chat = AsyncMock(
            side_effect=AIServiceException(provider="failing", message="Error"),
        )

        service = AIService()
        service._providers = {"failing": failing, "test": mock_provider}
        result = await service.chat(
            messages=[{"role": "user", "content": "Hi"}],
            fallback=["failing", "test"],
        )
        assert result["content"] == "test"

    @pytest.mark.asyncio
    async def test_chat_all_fail(self):
        failing = MagicMock()
        failing.name = "failing"
        failing.is_available.return_value = True
        failing.chat = AsyncMock(
            side_effect=AIServiceException(provider="failing", message="Error"),
        )

        service = AIService()
        service._providers = {"failing": failing}
        with pytest.raises(AIServiceException):
            await service.chat(messages=[{"role": "user", "content": "Hi"}])

    @pytest.mark.asyncio
    async def test_chat_unconfigured_provider(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        with pytest.raises(ProviderUnavailableException):
            await service.chat(messages=[{"role": "user", "content": "Hi"}], provider="nonexistent")

    def test_get_available_providers(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        available = service.get_available_providers()
        assert len(available) == 1
        assert available[0]["name"] == "test"
        assert available[0]["model"] == "test-model"
        assert available[0]["available"] is True

    @pytest.mark.asyncio
    async def test_close_clears_providers(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        mock_provider.close = AsyncMock()
        await service.close()
        assert len(service._providers) == 0

    @pytest.mark.asyncio
    async def test_chat_default_all_providers(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        result = await service.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result["content"] == "test"

    @pytest.mark.asyncio
    async def test_chat_unavailable_skipped(self):
        unavailable = MagicMock()
        unavailable.name = "unavail"
        unavailable.is_available.return_value = False
        unavailable.chat = AsyncMock()

        available = MagicMock()
        available.name = "avail"
        available.model = "avail-model"
        available.is_available.return_value = True
        available.chat = AsyncMock(return_value={"content": "ok"})

        service = AIService()
        service._providers = {"unavail": unavailable, "avail": available}
        result = await service.chat(messages=[{"role": "user", "content": "Hi"}])
        assert result["content"] == "ok"

    def test_providers_property(self, mock_provider):
        service = AIService()
        service._providers = {"test": mock_provider}
        assert "test" in service.providers
