from __future__ import annotations

import hashlib
import time
from typing import Any

from app.sync.interface import SyncAction, SyncChange


def compute_checksum(data: dict[str, Any]) -> str:
    import json

    raw = json.dumps(data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def make_change(
    entity_type: str,
    entity_id: str,
    action: SyncAction,
    data: dict[str, Any],
    version: int = 1,
    source: str = "local",
) -> SyncChange:
    return SyncChange(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        data=data,
        version=version,
        checksum=compute_checksum(data),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        source=source,
    )


def change_key(change: SyncChange) -> str:
    return f"{change['entity_type']}:{change['entity_id']}"


def is_older(change_a: SyncChange, change_b: SyncChange) -> bool:
    va = change_a.get("version", 0)
    vb = change_b.get("version", 0)
    return va < vb


def merge_changes(local: list[SyncChange], remote: list[SyncChange]) -> list[SyncChange]:
    merged: dict[str, SyncChange] = {}
    for c in local:
        merged[change_key(c)] = c
    for c in remote:
        key = change_key(c)
        if key in merged and is_older(merged[key], c) or key not in merged:
            merged[key] = c
    return list(merged.values())
