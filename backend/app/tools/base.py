from __future__ import annotations

import abc
from typing import Any


class BaseTool(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def parameters(self) -> dict:
        pass

    @abc.abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        pass

    def to_definition(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class BasePlugin(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def version(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def description(self) -> str:
        pass

    @abc.abstractmethod
    def get_tools(self) -> list[BaseTool]:
        pass

    async def initialize(self, config: dict | None = None) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    def is_enabled(self) -> bool:
        return True
