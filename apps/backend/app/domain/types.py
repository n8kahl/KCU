from __future__ import annotations

from typing import Any

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

    @staticmethod
    def default_band() -> ProbabilityBand:
        return ProbabilityBand(label="Loading", min_score=0, max_score=69)


class WhatIfResult(BaseModel):
    ticker: str
    probability: float
    band: ProbabilityBand
    eta_seconds: int | None = None
