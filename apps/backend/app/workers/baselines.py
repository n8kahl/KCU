from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.db.models import PercentileBaseline, Snapshot
from app.db.session import async_session
from app.domain.options.buckets import ETF_INDEX, contract_metadata, option_bucket
from app.services.baselines import baseline_service
from app.workers.celery_app import app


def _compute_percentiles(values: List[float]) -> Dict[str, float]:
    ordered = sorted(values)
    if not ordered:
        return {"p50": 0.0, "p75": 0.0, "p90": 0.0, "p95": 0.0}
    def pct(q: float) -> float:
        idx = int(round((len(ordered) - 1) * q))
        return float(ordered[idx])
    return {"p50": pct(0.5), "p75": pct(0.75), "p90": pct(0.9), "p95": pct(0.95)}


async def _upsert_percentile_rows(rows: List[dict]) -> None:
    if not rows:
        return
    async with async_session() as session:
        stmt = insert(PercentileBaseline).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PercentileBaseline.metric, PercentileBaseline.bucket_key],
            set_={
                "p50": stmt.excluded.p50,
                "p75": stmt.excluded.p75,
                "p90": stmt.excluded.p90,
                "p95": stmt.excluded.p95,
                "asof": stmt.excluded.asof,
            },
        )
        await session.execute(stmt)
        await session.commit()
    await baseline_service.refresh()


async def _build_option_baselines() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    metric_values: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    async with async_session() as session:
        stmt = select(Snapshot.ticker, Snapshot.options).where(Snapshot.ts >= cutoff)
        result = await session.execute(stmt)
        for ticker, options in result:
            if not options:
                continue
            contracts = options.get("contracts") or {}
            primary = contracts.get("primary")
            metadata = contract_metadata(primary)
            bucket = option_bucket(ticker, options.get("delta_target"), metadata.get("dte"), metadata.get("side"))
            spread = options.get("spread_pct")
            flicker = options.get("flicker_per_sec")
            ivr = options.get("ivr")
            vo_vol = options.get("vo_vol")
            if spread is not None:
                metric_values["spread_pct"][bucket].append(float(spread))
            if flicker is not None:
                metric_values["flicker_per_sec"][bucket].append(float(flicker))
            if ivr is not None:
                metric_values["iv_rank"][bucket].append(float(ivr))
            if vo_vol is not None:
                metric_values["vo_vol"][bucket].append(float(vo_vol))
    rows = []
    asof = datetime.now(timezone.utc).date()
    for metric, buckets in metric_values.items():
        for bucket_key, values in buckets.items():
            percentiles = _compute_percentiles(values)
            rows.append({"metric": metric, "bucket_key": bucket_key, **percentiles, "asof": asof})
    await _upsert_percentile_rows(rows)


async def _build_index_baselines() -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    metric_values: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    async with async_session() as session:
        stmt = select(Snapshot.ticker, Snapshot.market_micro).where(Snapshot.ts >= cutoff)
        result = await session.execute(stmt)
        for ticker, micro in result:
            if not micro:
                continue
            idx_symbol = ETF_INDEX.get(ticker, ticker)
            bucket = f"IDX:{idx_symbol}"
            for metric in ("minute_thrust", "micro_chop", "divergence_z", "sec_variance"):
                key = {
                    "minute_thrust": "minuteThrust",
                    "micro_chop": "microChop",
                    "divergence_z": "divergenceZ",
                    "sec_variance": "secVariance",
                }[metric]
                value = micro.get(key)
                if value is not None:
                    metric_values[metric][bucket].append(float(value))
    rows = []
    asof = datetime.now(timezone.utc).date()
    for metric, buckets in metric_values.items():
        for bucket_key, values in buckets.items():
            percentiles = _compute_percentiles(values)
            rows.append({"metric": metric, "bucket_key": bucket_key, **percentiles, "asof": asof})
    await _upsert_percentile_rows(rows)


@app.task(name="app.workers.baselines.build_option_percentiles")
def build_option_percentiles() -> str:
    asyncio.run(_build_option_baselines())
    return datetime.now(timezone.utc).isoformat()


@app.task(name="app.workers.baselines.build_index_percentiles")
def build_index_percentiles() -> str:
    asyncio.run(_build_index_baselines())
    return datetime.now(timezone.utc).isoformat()
