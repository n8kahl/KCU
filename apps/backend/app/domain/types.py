from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProbabilityBand(BaseModel):
    label: str
    min_score: float
    max_score: float

    @staticmethod
    def from_score(score: float) -> "ProbabilityBand":
        if score >= 80:
            return ProbabilityBand(label="EntryReady", min_score=80, max_score=100)
        if score >= 70:
            return ProbabilityBand(label="Armed", min_score=70, max_score=79)
        return ProbabilityBand(label="Loading", min_score=0, max_score=69)


class LevelDelta(BaseModel):
    dollars: float | None = None
    percent: float | None = None
    direction: Literal["above", "below", "at"] | None = None
    at_entry: bool = False


class KeyLevel(BaseModel):
    label: str
    price: float


class BarPoint(BaseModel):
    o: float | None = None
    h: float | None = None
    l: float | None = None
    c: float | None = None
    v: float | None = None
    t: str | None = None


class OptionTopContract(BaseModel):
    contract: str
    ticker: str
    expiry: str | None = None
    strike: float | None = None
    type: Literal["call", "put"] | None = None
    bid: float | None = None
    ask: float | None = None
    mid: float | None = None
    delta: float | None = None
    oi: int | None = None
    spread_quality: str | None = None


class TileState(BaseModel):
    symbol: str
    regime: str
    probability_to_action: float = Field(ge=0, le=1)
    band: ProbabilityBand
    confidence: dict[str, float]
    breakdown: list[dict[str, Any]]
    options: dict[str, Any]
    rationale: dict[str, list[str]]
    admin: dict[str, Any]
    timestamps: dict[str, str]
    eta_seconds: int | None = None
    penalties: dict[str, float]
    bonuses: dict[str, float]
    history: list[dict[str, Any]]
    grade: str = "C"
    confidence_score: int = 0
    delta_to_entry: LevelDelta | None = None
    key_level_label: str | None = None
    bars: list[BarPoint] = Field(default_factory=list)
    ema8: list[float] = Field(default_factory=list)
    ema21: list[float] = Field(default_factory=list)
    vwap: list[float] = Field(default_factory=list)
    key_levels: list[KeyLevel] = Field(default_factory=list)
    patience_candle: bool = False
    options_top3: list[OptionTopContract] = Field(default_factory=list)

    @staticmethod
    def default_band() -> ProbabilityBand:
        return ProbabilityBand(label="Loading", min_score=0, max_score=69)


class WhatIfResult(BaseModel):
    ticker: str
    probability: float
    band: ProbabilityBand
    eta_seconds: int | None = None
