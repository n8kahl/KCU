from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.services.timing import get_timing_context


@dataclass
class TPLevel:
    price: float
    snapped_to: str
    label: str
    distance_pct: float
    hit: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RunnerState:
    trail: float
    label: str
    extended_to: Optional[float] = None
    continuation_prob: float = 0.0
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TPPlan:
    symbol: str
    direction: str
    entry: float
    started_at: str
    tp1: TPLevel
    tp2: TPLevel
    runner: RunnerState
    timing: dict
    reasons: List[str]

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "entry": self.entry,
            "started_at": self.started_at,
            "tp1": self.tp1.to_dict(),
            "tp2": self.tp2.to_dict(),
            "runner": self.runner.to_dict(),
            "timing": self.timing,
            "reasons": self.reasons,
        }


class TPManager:
    def __init__(self) -> None:
        self._plans: Dict[str, TPPlan] = {}
        self._contexts: Dict[str, dict] = {}
        self._lock = asyncio.Lock()

    async def reset(self) -> None:  # pragma: no cover - testing helper
        async with self._lock:
            self._plans.clear()
            self._contexts.clear()

    async def update_context(self, symbol: str, context: dict) -> None:
        async with self._lock:
            existing = self._contexts.get(symbol, {})
            existing.update(context)
            self._contexts[symbol] = existing

    async def get_plan(self, symbol: str) -> Optional[dict]:
        async with self._lock:
            plan = self._plans.get(symbol)
            return plan.to_dict() if plan else None

    async def stop(self, symbol: str) -> None:
        async with self._lock:
            self._plans.pop(symbol, None)

    async def start(
        self,
        symbol: str,
        *,
        entry: float,
        direction: str,
        regime: str,
        liquidity_risk: float | None,
        minute_thrust: float | None,
        divergence: float | None,
        timing: dict | None,
    ) -> dict:
        async with self._lock:
            context = self._contexts.get(symbol)
            if not context:
                raise ValueError("No context available for symbol")
            plan = self._build_plan(
                symbol,
                entry,
                direction,
                regime,
                liquidity_risk or 50,
                minute_thrust or 0.0,
                divergence or 0.0,
                timing or get_timing_context(datetime.now(timezone.utc)),
                context,
            )
            self._plans[symbol] = plan
            return plan.to_dict()

    async def on_tick(
        self,
        symbol: str,
        price: float | None,
        probability: float,
        liquidity_risk: float | None,
        market_micro: dict,
        timing: dict,
    ) -> Optional[dict]:
        async with self._lock:
            plan = self._plans.get(symbol)
            if not plan:
                return None
            if price is None:
                price = self._contexts.get(symbol, {}).get("last_price")
            if price is None:
                return plan.to_dict()
            self._contexts.setdefault(symbol, {})["last_price"] = price
            self._update_plan(plan, price, probability, liquidity_risk or 0, market_micro)
            plan.timing = timing
            return plan.to_dict()

    def _build_plan(
        self,
        symbol: str,
        entry: float,
        direction: str,
        regime: str,
        liquidity_risk: float,
        minute_thrust: float,
        divergence: float,
        timing: dict,
        context: dict,
    ) -> TPPlan:
        levels = context.get("levels") or []
        atr = context.get("atr") or max(entry * 0.004, 0.5)
        ema = context.get("ema") or entry
        direction = direction.lower()
        multipliers = self._multipliers_for(regime, timing.get("window"))
        tp1_target = entry + self._sign(direction) * atr * multipliers[0]
        tp2_target = entry + self._sign(direction) * atr * multipliers[1]
        snapped_tp1 = self._snap_level(tp1_target, direction, levels)
        snapped_tp2 = self._snap_level(tp2_target, direction, levels)
        runner_trail = ema - self._sign(direction) * (0.35 * atr)
        reasons = self._build_reasons(liquidity_risk, minute_thrust, divergence)
        plan = TPPlan(
            symbol=symbol,
            direction=direction,
            entry=round(entry, 2),
            started_at=datetime.now(timezone.utc).isoformat(),
            tp1=self._level_to_plan(snapped_tp1, tp1_target, entry, direction, "TP1"),
            tp2=self._level_to_plan(snapped_tp2, tp2_target, entry, direction, "TP2"),
            runner=RunnerState(
                trail=round(runner_trail, 2),
                label="EMA8 ± ATR(2m) cushion",
                continuation_prob=0.0,
                reasons=reasons,
            ),
            timing=timing,
            reasons=reasons,
        )
        return plan

    def _update_plan(
        self,
        plan: TPPlan,
        price: float,
        probability: float,
        liquidity_risk: float,
        market_micro: dict,
    ) -> None:
        for level in (plan.tp1, plan.tp2):
            if plan.direction == "long" and price >= level.price:
                level.hit = True
            elif plan.direction == "short" and price <= level.price:
                level.hit = True
        plan.runner.continuation_prob = probability
        reasons = []
        if market_micro.get("minuteThrust", 0) > 0:
            reasons.append("Index thrust ✓")
        if abs(market_micro.get("divergenceZ", 0)) <= 0.7:
            reasons.append("Divergence < 0.7σ")
        if liquidity_risk < 60:
            reasons.append("Liquidity green")
        plan.runner.reasons = reasons or plan.runner.reasons
        extend_conditions = (
            plan.runner.continuation_prob >= 0.72
            and liquidity_risk < 60
            and market_micro.get("minuteThrust", 0) > 0
            and abs(market_micro.get("divergenceZ", 0)) <= 0.7
        )
        if extend_conditions and not plan.runner.extended_to:
            plan.runner.extended_to = round(plan.tp2.price + self._sign(plan.direction) * 0.5 * (plan.tp2.price - plan.entry), 2)

    def _multipliers_for(self, regime: str, window: str | None) -> tuple[float, float]:
        base = {
            "Calm": (0.45, 0.9),
            "Normal": (0.5, 1.0),
            "Fast": (0.6, 1.25),
        }.get(regime, (0.5, 1.0))
        if window == "Midday Compression":
            return (0.4, 0.9)
        if window == "Late Day":
            return (0.45, 0.95)
        return base

    def _snap_level(self, target: float, direction: str, levels: List[dict]) -> dict:
        direction_sign = self._sign(direction)
        candidates = []
        for level in levels:
            price = level.get("price")
            if price is None:
                continue
            if direction_sign > 0 and price >= target:
                candidates.append(level)
            elif direction_sign < 0 and price <= target:
                candidates.append(level)
        if not candidates:
            return {"price": round(target, 2), "label": "Synthetic", "snapped_to": "Synthetic"}
        if direction_sign > 0:
            best = min(candidates, key=lambda lvl: lvl["price"])
        else:
            best = max(candidates, key=lambda lvl: lvl["price"])
        return {"price": round(best["price"], 2), "label": best["label"], "snapped_to": best["label"]}

    def _level_to_plan(self, level: dict, target: float, entry: float, direction: str, label: str) -> TPLevel:
        distance = abs(level["price"] - entry)
        pct = distance / entry * 100 if entry else distance
        snapped_label = level.get("snapped_to", level.get("label", "Level"))
        return TPLevel(price=level["price"], snapped_to=snapped_label, label=f"{label} @{snapped_label}", distance_pct=round(pct, 2))

    def _sign(self, direction: str) -> int:
        return 1 if direction.lower() == "long" else -1

    def _build_reasons(self, liquidity_risk: float, minute_thrust: float, divergence: float) -> List[str]:
        reasons = []
        if minute_thrust > 0:
            reasons.append("Index thrust supportive")
        if abs(divergence) <= 0.7:
            reasons.append("ETF/index divergence within band")
        if liquidity_risk < 60:
            reasons.append("Liquidity favorable")
        if not reasons:
            reasons.append("Monitoring macro alignment")
        return reasons


tp_manager = TPManager()
