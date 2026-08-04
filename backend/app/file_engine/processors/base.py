from __future__ import annotations

import abc
from typing import Any

from app.file_engine.interface import FileMetadata  # noqa: TC001


class Processor(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def supported_extensions(self) -> set[str]:
        pass

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        return metadata

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        return ""

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        return {}

    def validate(self, data: bytes, metadata: FileMetadata) -> bool:
        return True


class ChainProcessor(Processor):
    def __init__(self, processors: list[Processor]) -> None:
        self._processors = processors
        self._extensions: set[str] = set()
        for p in processors:
            self._extensions.update(p.supported_extensions())

    @property
    def name(self) -> str:
        return "chain"

    def supported_extensions(self) -> set[str]:
        return self._extensions

    async def process(self, data: bytes, metadata: FileMetadata) -> FileMetadata:
        for p in self._processors:
            metadata = await p.process(data, metadata)
        return metadata

    async def extract_text(self, data: bytes, metadata: FileMetadata) -> str:
        texts = []
        for p in self._processors:
            text = await p.extract_text(data, metadata)
            if text:
                texts.append(text)
        return "\n".join(texts)

    async def extract_metadata(self, data: bytes, metadata: FileMetadata) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for p in self._processors:
            result.update(await p.extract_metadata(data, metadata))
        return result
