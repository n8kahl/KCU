from __future__ import annotations

from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.adapters.discord import send_alert
from app.core.settings import settings

router = APIRouter()


class AlertAction(str, Enum):
    enter = "enter"
    take_profit = "take_profit"
    add = "add"
    trim = "trim"
    exit = "exit"


class AlertRequest(BaseModel):
    action: AlertAction
    symbol: str = Field(min_length=1, max_length=8)
    contract: str = Field(min_length=3, max_length=32)
    price: float = Field(gt=0)
    grade: str = Field(min_length=1, max_length=3)
    confidence: int = Field(ge=0, le=100)
    level: str = Field(min_length=1, max_length=120)
    stop: float = Field(gt=0)
    target: float = Field(gt=0)
    note: str | None = Field(default=None, max_length=480)


def _format_alert(payload: AlertRequest) -> str:
    action_label = payload.action.value.replace("_", " ").title()
    base = (
        f"[{action_label}] {payload.symbol.upper()} {payload.contract} @ ${payload.price:.2f} "
        f"· Grade {payload.grade.upper()} · Conf {payload.confidence}%"
    )
    level_blurb = f"Level {payload.level} · Stop {payload.stop:.2f} · Target {payload.target:.2f}"
    note = f" — {payload.note.strip()}" if payload.note else ""
    return f"{base} · {level_blurb}{note}"


@router.post("/alerts")
async def create_alert(payload: AlertRequest) -> dict[str, str]:
    content = _format_alert(payload)
    await send_alert(settings.discord_webhook_url, content)
    return {"status": "ok"}
