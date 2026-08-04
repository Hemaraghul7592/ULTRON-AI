from __future__ import annotations

import os
import shutil
from typing import Any

from app.file_engine.errors import FileNotFoundError, FilePermissionError
from app.file_engine.interface import StorageProvider

_DEFAULT_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "storage",
)


class LocalStorage(StorageProvider):
    def __init__(self, root: str = _DEFAULT_ROOT) -> None:
        self._root = root
        os.makedirs(self._root, exist_ok=True)

    @property
    def name(self) -> str:
        return "local"

    @property
    def root(self) -> str:
        return self._root

    def _resolve(self, path: str) -> str:
        resolved = os.path.normpath(os.path.join(self._root, path))
        if not resolved.startswith(os.path.normpath(self._root)):
            raise FilePermissionError(f"Path traversal denied: {path}")
        return resolved

    async def save(self, path: str, data: bytes) -> str:
        full = self._resolve(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as f:
            f.write(data)
        return path

    async def load(self, path: str) -> bytes:
        full = self._resolve(path)
        if not os.path.exists(full):
            raise FileNotFoundError(f"File not found: {path}")
        with open(full, "rb") as f:
            return f.read()

    async def delete(self, path: str) -> bool:
        full = self._resolve(path)
        if not os.path.exists(full):
            return False
        os.remove(full)
        parent = os.path.dirname(full)
        try:
            os.rmdir(parent)
        except OSError:
            pass
        return True

    async def exists(self, path: str) -> bool:
        full = self._resolve(path)
        return os.path.exists(full)

    async def move(self, source: str, destination: str) -> bool:
        src = self._resolve(source)
        dst = self._resolve(destination)
        if not os.path.exists(src):
            return False
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        return True

    async def copy(self, source: str, destination: str) -> bool:
        src = self._resolve(source)
        dst = self._resolve(destination)
        if not os.path.exists(src):
            return False
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return True

    async def list_files(self, prefix: str = "") -> list[str]:
        base = self._resolve(prefix) if prefix else self._root
        if not os.path.exists(base):
            return []
        results: list[str] = []
        for root, _dirs, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, self._root)
                results.append(rel)
        return sorted(results)

    async def get_metadata(self, path: str) -> dict[str, Any]:
        full = self._resolve(path)
        if not os.path.exists(full):
            raise FileNotFoundError(f"File not found: {path}")
        stat = os.stat(full)
        return {
            "size": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "mode": stat.st_mode,
        }
