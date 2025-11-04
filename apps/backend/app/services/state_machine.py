from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Dict

from app.domain.templates import get_template


@dataclass
class TileBand:
    label: str


class StateMachine:
    def __init__(self) -> None:
        self._policy = {"mode": "Standard", "overrides": {}}
        self._overrides: Dict[str, dict] = {}

    def set_policy(self, mode: str, overrides: dict) -> None:
        self._policy = {"mode": mode, "overrides": overrides}

    def apply_override(self, symbol: str, override: dict) -> None:
        self._overrides[symbol] = override

    def derive_state(self, symbol: str, score: float) -> TileBand:
        now = datetime.now(timezone.utc).time()
        if time(9, 30) <= now <= time(9, 35):
            return TileBand("Paused")
        template = get_template("Normal", self._policy["mode"])
        loading, armed = 70 * template["modifier"], 80 * template["modifier"]
        if score >= armed:
            label = "EntryReady"
        elif score >= loading:
            label = "Armed"
        else:
            label = "Loading"
        return TileBand(label)
