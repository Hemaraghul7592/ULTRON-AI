from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any


class StoredFile:
    def __init__(
        self,
        filename: str,
        mime_type: str,
        extension: str,
        size: int,
        sha256: str,
        storage_path: str,
        storage_provider: str = "local",
        file_id: str | None = None,
        created_at: str | None = None,
        width: int | None = None,
        height: int | None = None,
        duration: float | None = None,
        pages: int | None = None,
        ocr_text: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        self.file_id = file_id or str(uuid.uuid4())
        self.filename = filename
        self.mime_type = mime_type
        self.extension = extension
        self.size = size
        self.sha256 = sha256
        self.storage_path = storage_path
        self.storage_provider = storage_provider
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.width = width
        self.height = height
        self.duration = duration
        self.pages = pages
        self.ocr_text = ocr_text
        self.extra = extra or {}

    def to_metadata(self) -> dict[str, Any]:
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "size": self.size,
            "sha256": self.sha256,
            "storage_path": self.storage_path,
            "storage_provider": self.storage_provider,
            "created_at": self.created_at,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "pages": self.pages,
            "ocr_text": self.ocr_text,
            "extra": self.extra,
        }

    @classmethod
    def from_metadata(cls, data: dict[str, Any]) -> StoredFile:
        return cls(
            filename=data["filename"],
            mime_type=data["mime_type"],
            extension=data["extension"],
            size=data["size"],
            sha256=data["sha256"],
            storage_path=data["storage_path"],
            storage_provider=data.get("storage_provider", "local"),
            file_id=data.get("file_id"),
            created_at=data.get("created_at"),
            width=data.get("width"),
            height=data.get("height"),
            duration=data.get("duration"),
            pages=data.get("pages"),
            ocr_text=data.get("ocr_text"),
            extra=data.get("extra"),
        )
