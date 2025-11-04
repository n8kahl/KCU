from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional

from sqlalchemy import select

from app.db.models import PercentileBaseline
from app.db.session import async_session


@dataclass
class PercentileSnapshot:
    p50: float
    p75: float
    p90: float
    p95: float
    asof: date


class BaselineService:
    def __init__(self) -> None:
        self._cache: Dict[tuple[str, str], PercentileSnapshot] = {}
        self._lock = asyncio.Lock()
        self._loaded = False
        self._logger = logging.getLogger(__name__)

    async def refresh(self) -> None:
        async with self._lock:
            try:
                async with async_session() as session:
                    result = await session.execute(select(PercentileBaseline))
                    rows = result.scalars().all()
                self._cache = {
                    (row.metric, row.bucket_key): PercentileSnapshot(
                        p50=row.p50,
                        p75=row.p75,
                        p90=row.p90,
                        p95=row.p95,
                        asof=row.asof,
                    )
                    for row in rows
                }
            except Exception as exc:  # pragma: no cover - optional DB path
                self._logger.warning("baseline-refresh-failed", extra={"error": str(exc)})
                self._cache = {}
            self._loaded = True

    async def get_percentiles(self, metric: str, bucket_key: str) -> Optional[PercentileSnapshot]:
        if not self._loaded:
            await self.refresh()
        return self._cache.get((metric, bucket_key))


baseline_service = BaselineService()


def percentile_rank(value: float | None, baseline: PercentileSnapshot | None) -> Optional[float]:
    if value is None or baseline is None:
        return None
    points = [
        (baseline.p50, 0.5),
        (baseline.p75, 0.75),
        (baseline.p90, 0.9),
        (baseline.p95, 0.95),
    ]
    if value <= points[0][0]:
        return 0.5
    for (low_val, low_pct), (high_val, high_pct) in zip(points, points[1:]):
        if value <= high_val:
            span = high_val - low_val or 1e-6
            fraction = (value - low_val) / span
            return round(low_pct + (high_pct - low_pct) * fraction, 4)
    return 0.99


def percentile_to_label(rank: Optional[float]) -> str:
    if rank is None:
        return "p--"
    return f"p{int(rank * 100):02d}"
