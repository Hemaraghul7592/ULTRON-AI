from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator


@dataclass
class FileMetadata:
    filename: str
    mime_type: str
    extension: str
    size: int
    sha256: str
    storage_path: str
    storage_provider: str = "local"
    created_at: str = ""
    modified_at: str = ""
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    pages: int | None = None
    ocr_text: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class StorageProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    async def save(self, path: str, data: bytes) -> str:
        pass

    @abc.abstractmethod
    async def load(self, path: str) -> bytes:
        pass

    @abc.abstractmethod
    async def delete(self, path: str) -> bool:
        pass

    @abc.abstractmethod
    async def exists(self, path: str) -> bool:
        pass

    @abc.abstractmethod
    async def move(self, source: str, destination: str) -> bool:
        pass

    @abc.abstractmethod
    async def copy(self, source: str, destination: str) -> bool:
        pass

    @abc.abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        pass

    @abc.abstractmethod
    async def get_metadata(self, path: str) -> dict[str, Any]:
        pass
