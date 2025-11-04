from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domain.types import TileState

_snapshots: list[dict[str, Any]] = []


def persist_snapshot(tile: TileState) -> uuid.UUID:
    record = tile.model_dump()
    record["id"] = str(uuid.uuid4())
    record["ts"] = datetime.now(timezone.utc).isoformat()
    _snapshots.append(record)
    return uuid.UUID(record["id"])


def latest(limit: int = 10) -> list[dict[str, Any]]:
    return list(reversed(_snapshots[-limit:]))
