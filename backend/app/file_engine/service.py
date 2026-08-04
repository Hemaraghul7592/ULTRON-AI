from __future__ import annotations

import os
import time
from typing import Any

from app.file_engine.errors import (
    DuplicateFileError,
    FileNotFoundError,  # noqa: A004
    InvalidFileTypeError,
    ProcessingError,
    StorageError,
)
from app.file_engine.interface import FileMetadata, StorageProvider
from app.file_engine.models import StoredFile
from app.file_engine.processors.audio import AudioProcessor
from app.file_engine.processors.base import Processor  # noqa: TC001
from app.file_engine.processors.image import ImageProcessor
from app.file_engine.processors.ocr import OCRProcessor
from app.file_engine.processors.pdf import PDFProcessor
from app.file_engine.processors.text import TextProcessor
from app.file_engine.utils import (
    get_extension,
    get_storage_subpath,
    guess_mime_type,
    is_supported_filename,
    safe_filename,
    sha256_hash,
)

_DEFAULT_MAX_SIZE = 50 * 1024 * 1024


class FileService:
    def __init__(
        self,
        storage: StorageProvider,
        max_size: int = _DEFAULT_MAX_SIZE,
        deduplicate: bool = True,
    ) -> None:
        self._storage = storage
        self._max_size = max_size
        self._deduplicate = deduplicate
        self._processors: dict[str, Processor] = {}
        self._register_processors()

    def _register_processors(self) -> None:
        processors: list[Processor] = [
            TextProcessor(),
            ImageProcessor(),
            PDFProcessor(),
            AudioProcessor(),
            OCRProcessor(),
        ]
        for p in processors:
            for ext in p.supported_extensions():
                self._processors[ext] = p

    @property
    def storage(self) -> StorageProvider:
        return self._storage

    async def save(
        self,
        data: bytes,
        filename: str,
        mime_type: str | None = None,
        run_ocr: bool = False,
    ) -> StoredFile:
        if not data:
            raise ValueError("Cannot save empty file")

        if len(data) > self._max_size:
            raise InvalidFileTypeError(
                message=f"File too large ({len(data)} bytes, max {self._max_size})",
                path=filename,
            )

        safe_name = safe_filename(filename)
        ext = get_extension(filename)
        if not is_supported_filename(filename):
            raise InvalidFileTypeError(
                message=f"Unsupported file type: {ext}",
                path=filename,
            )

        resolved_mime = mime_type or guess_mime_type(filename)
        file_hash = sha256_hash(data)

        if self._deduplicate:
            existing = await self._find_by_hash(file_hash)
            if existing:
                raise DuplicateFileError(
                    message=f"Duplicate file (SHA-256: {file_hash[:16]}...)",
                    path=filename,
                )

        storage_path = get_storage_subpath(file_hash, safe_name)

        try:
            actual_path = await self._storage.save(storage_path, data)
        except Exception as e:
            raise StorageError(message="Failed to save file", path=storage_path) from e

        meta = FileMetadata(
            filename=safe_name,
            mime_type=resolved_mime,
            extension=ext,
            size=len(data),
            sha256=file_hash,
            storage_path=actual_path,
            storage_provider=self._storage.name,
        )

        meta = await self._process_file(data, meta, run_ocr=run_ocr)

        return StoredFile(
            filename=meta.filename,
            mime_type=meta.mime_type,
            extension=meta.extension,
            size=meta.size,
            sha256=meta.sha256,
            storage_path=meta.storage_path,
            storage_provider=meta.storage_provider,
            width=meta.width,
            height=meta.height,
            duration=meta.duration,
            pages=meta.pages,
            ocr_text=meta.ocr_text,
            extra=meta.extra,
        )

    async def load(self, file_id_or_path: str) -> bytes:
        path = file_id_or_path
        if not await self._storage.exists(path):
            raise FileNotFoundError(message="File not found", path=path)
        try:
            return await self._storage.load(path)
        except Exception as e:
            raise StorageError(message=f"Failed to load file: {e}", path=path) from e

    async def delete(self, file_id_or_path: str) -> bool:
        path = file_id_or_path
        try:
            return await self._storage.delete(path)
        except Exception as e:
            raise StorageError(message=f"Failed to delete file: {e}", path=path) from e

    async def copy(self, source_path: str, dest_filename: str) -> StoredFile:
        if not await self._storage.exists(source_path):
            raise FileNotFoundError(message="Source file not found", path=source_path)
        data = await self._storage.load(source_path)
        return await self.save(data=data, filename=dest_filename)

    async def move(self, source_path: str, dest_filename: str) -> StoredFile:
        new_file = await self.copy(source_path, dest_filename)
        await self._storage.delete(source_path)
        return new_file

    async def exists(self, path: str) -> bool:
        return await self._storage.exists(path)

    async def list_files(self, prefix: str = "") -> list[str]:
        return await self._storage.list_files(prefix)

    async def get_metadata(self, path: str) -> dict[str, Any]:
        try:
            return await self._storage.get_metadata(path)
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(message=f"Failed to get metadata: {e}", path=path) from e

    async def extract_text(self, data: bytes, filename: str) -> str:
        ext = get_extension(filename)
        processor = self._processors.get(ext)
        if processor is None:
            return ""
        meta = FileMetadata(
            filename=safe_filename(filename),
            mime_type=guess_mime_type(filename),
            extension=ext,
            size=len(data),
            sha256=sha256_hash(data),
            storage_path="",
        )
        try:
            return await processor.extract_text(data, meta)
        except Exception as e:
            raise ProcessingError(
                message=f"Text extraction failed: {e}",
                path=filename,
            ) from e

    async def _process_file(
        self,
        data: bytes,
        meta: FileMetadata,
        run_ocr: bool = False,
    ) -> FileMetadata:
        ext = meta.extension
        processor = self._processors.get(ext)
        if processor is None:
            return meta
        try:
            meta = await processor.process(data, meta)
        except Exception as e:
            raise ProcessingError(
                message=f"File processing failed: {e}",
                path=meta.filename,
            ) from e
        return meta

    async def _find_by_hash(self, sha256: str) -> StoredFile | None:
        prefix = sha256[:4]
        files = await self._storage.list_files(prefix)
        from contextlib import suppress

        for file_path in files:
            with suppress(Exception):
                data = await self._storage.load(file_path)
                if sha256_hash(data) == sha256:
                    ext = get_extension(file_path)
                    return StoredFile(
                        filename=os.path.basename(file_path),
                        mime_type=guess_mime_type(file_path),
                        extension=ext,
                        size=len(data),
                        sha256=sha256,
                        storage_path=file_path,
                    )
        return None

    async def health_check(self) -> dict[str, Any]:
        storage_ok = False
        from contextlib import suppress

        with suppress(Exception):
            test_path = f".health_{int(time.time())}"
            await self._storage.save(test_path, b"health")
            storage_ok = True
            await self._storage.delete(test_path)
        return {
            "storage": self._storage.name,
            "storage_ok": storage_ok,
            "max_size": self._max_size,
            "deduplicate": self._deduplicate,
            "registered_processors": list(self._processors.keys()),
        }
