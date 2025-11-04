from __future__ import annotations

from datetime import date, datetime
import uuid

from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Candle(Base):
    __tablename__ = "candles"

    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    timeframe: Mapped[str] = mapped_column(String(8), primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[float] = mapped_column(Numeric(12, 4))
    high: Mapped[float] = mapped_column(Numeric(12, 4))
    low: Mapped[float] = mapped_column(Numeric(12, 4))
    close: Mapped[float] = mapped_column(Numeric(12, 4))
    volume: Mapped[int] = mapped_column(BigInteger)


class Levels(Base):
    __tablename__ = "levels"

    day: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(16), primary_key=True)
    premarket_high: Mapped[float | None] = mapped_column(Numeric(12, 4))
    premarket_low: Mapped[float | None] = mapped_column(Numeric(12, 4))
    prior_high: Mapped[float | None] = mapped_column(Numeric(12, 4))
    prior_low: Mapped[float | None] = mapped_column(Numeric(12, 4))
    prior_close: Mapped[float | None] = mapped_column(Numeric(12, 4))
    open_print: Mapped[float | None] = mapped_column(Numeric(12, 4))


class OptionSnapshot(Base):
    __tablename__ = "option_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    contract: Mapped[str] = mapped_column(String(32))
    bid: Mapped[float] = mapped_column(Numeric(12, 4))
    ask: Mapped[float] = mapped_column(Numeric(12, 4))
    mid: Mapped[float] = mapped_column(Numeric(12, 4))
    oi: Mapped[int | None]
    vol: Mapped[int | None]
    iv: Mapped[float | None]
    delta: Mapped[float | None]
    gamma: Mapped[float | None]
    theta: Mapped[float | None]
    vega: Mapped[float | None]


class Snapshot(Base):
    __tablename__ = "snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ticker: Mapped[str] = mapped_column(String(16), index=True)
    regime: Mapped[str] = mapped_column(String(16))
    score: Mapped[float] = mapped_column(Numeric(6, 2))
    prob: Mapped[dict] = mapped_column(JSONB)
    bands: Mapped[dict] = mapped_column(JSONB)
    breakdown: Mapped[dict] = mapped_column(JSONB)
    options: Mapped[dict] = mapped_column(JSONB)
    orb: Mapped[dict] = mapped_column(JSONB)
    patience: Mapped[dict] = mapped_column(JSONB)
    penalties: Mapped[dict] = mapped_column(JSONB)
    bonuses: Mapped[dict] = mapped_column(JSONB)
    state: Mapped[str] = mapped_column(String(32))
    rationale: Mapped[dict] = mapped_column(JSONB)
    market_micro: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class PercentileBaseline(Base):
    __tablename__ = "percentile_baselines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    bucket_key: Mapped[str] = mapped_column(String(128), index=True)
    p50: Mapped[float] = mapped_column(Float)
    p75: Mapped[float] = mapped_column(Float)
    p90: Mapped[float] = mapped_column(Float)
    p95: Mapped[float] = mapped_column(Float)
    asof: Mapped[date] = mapped_column(Date, index=True)
