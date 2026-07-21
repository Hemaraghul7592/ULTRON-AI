from __future__ import annotations


def escape_like(string: str) -> str:
    return string.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
