from __future__ import annotations

import hashlib
import os
import re
import tempfile
import uuid
from collections.abc import AsyncIterator  # noqa: TC003
from contextlib import asynccontextmanager, suppress
from pathlib import Path

from app.file_engine.errors import InvalidFileTypeError

MAX_FILENAME_LENGTH = 255
SAFE_FILENAME_RE = re.compile(r"[^\w\.\-]")

EXTENSION_MIME_MAP: dict[str, str] = {
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".json": "application/json",
    ".csv": "text/csv",
    ".xml": "application/xml",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".m4a": "audio/mp4",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".zip": "application/zip",
    ".tar": "application/x-tar",
    ".gz": "application/gzip",
}

MIME_EXTENSION_MAP: dict[str, str] = {v: k for k, v in EXTENSION_MIME_MAP.items()}

SUPPORTED_EXTENSIONS: set[str] = set(EXTENSION_MIME_MAP.keys())

TEXT_EXTENSIONS: set[str] = {".txt", ".md", ".json", ".csv", ".xml", ".yaml", ".yml"}
IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}
AUDIO_EXTENSIONS: set[str] = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
DOCUMENT_EXTENSIONS: set[str] = {".pdf", ".docx"}


def sha256_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_filename(filename: str) -> str:
    name = SAFE_FILENAME_RE.sub("_", filename)
    name = name.strip("._")
    if not name:
        name = f"unnamed_{uuid.uuid4().hex[:8]}"
    if len(name) > MAX_FILENAME_LENGTH:
        base, ext = os.path.splitext(name)
        base = base[: MAX_FILENAME_LENGTH - len(ext) - 1]
        name = f"{base}{ext}"
    return name


def get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def guess_mime_type(filename: str) -> str:
    ext = get_extension(filename)
    return EXTENSION_MIME_MAP.get(ext, "application/octet-stream")


def guess_extension(mime_type: str) -> str:
    return MIME_EXTENSION_MAP.get(mime_type, ".bin")


def is_supported_extension(ext: str) -> bool:
    return ext.lower() in SUPPORTED_EXTENSIONS


def is_supported_filename(filename: str) -> bool:
    ext = get_extension(filename)
    return is_supported_extension(ext)


def validate_mime_type(mime_type: str, allowed: set[str] | None = None) -> str:
    if allowed is not None and mime_type not in allowed:
        raise InvalidFileTypeError(
            message=f"Unsupported MIME type: {mime_type}",
            path="",
        )
    return mime_type


def validate_extension(ext: str) -> str:
    if not is_supported_extension(ext):
        raise InvalidFileTypeError(
            message=f"Unsupported file extension: {ext}",
            path="",
        )
    return ext


def validate_filename(filename: str) -> str:
    ext = get_extension(filename)
    validate_extension(ext)
    return safe_filename(filename)


def get_storage_subpath(sha256: str, filename: str) -> str:
    prefix = sha256[:4]
    safe = safe_filename(filename)
    return f"{prefix}/{safe}"


@asynccontextmanager
async def temp_file(suffix: str = "") -> AsyncIterator[Path]:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    try:
        yield Path(path)
    finally:
        with suppress(OSError):
            os.unlink(path)


def format_size(size: int) -> str:
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"
