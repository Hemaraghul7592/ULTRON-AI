from __future__ import annotations

from app.ai.providers.openai_compatible import OpenAICompatibleProvider


class GrokProvider(OpenAICompatibleProvider):
    BASE_URL = "https://api.x.ai/v1"

    def __init__(self, api_key: str, model: str = "grok-2-latest") -> None:
        super().__init__(name="grok", api_key=api_key, model=model)

    def get_models(self) -> list[str]:
        return [
            "grok-2-latest",
            "grok-2-vision-latest",
            "grok-beta",
        ]
