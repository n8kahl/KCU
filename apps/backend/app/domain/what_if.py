from __future__ import annotations

from app.domain.scoring.probability import aggregate_probability
from app.domain.templates import get_template
from app.domain.types import ProbabilityBand, WhatIfResult


def evaluate_what_if(ticker: str, deltas: dict[str, float | bool]) -> WhatIfResult:
    contributions = {
        "TrendStack": 0.75,
        "Levels": 0.65,
        "Patience": 0.6,
        "ORB": 0.55,
        "Market": 0.7,
        "Options": 0.5,
    }
    penalties = {"chop": -7}
    bonuses = {"king_queen": 8}

    if deltas.get("spreadShrinksTo"):
        bonuses["liquidity"] = 3
    if deltas.get("orbRetestConfirms"):
        bonuses["orb_retest"] = 5
    if isinstance(deltas.get("ivChange"), (int, float)) and deltas["ivChange"] < 0:
        bonuses["iv_relief"] = 2

    probability, band = aggregate_probability(contributions, penalties, bonuses)
    template = get_template("Normal")
    eta = int(sum(template["debounce"]) / 2)
    return WhatIfResult(ticker=ticker, probability=probability, band=band, eta_seconds=eta)
