from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.core.security import verify_api_key
from app.services.state_machine import StateMachine

router = APIRouter(prefix="/admin", dependencies=[Depends(verify_api_key)])
state_machine = StateMachine()


class PolicyPayload(BaseModel):
    mode: str = Field(..., pattern="^(Conservative|Standard|Aggressive)$")
    overrides: dict[str, float | int]


class OverridePayload(BaseModel):
    symbol: str
    snoozeMin: int | None = None
    kill: bool | None = None
    confirm: bool | None = None


@router.post("/policy")
async def update_policy(payload: PolicyPayload) -> dict[str, str | dict[str, float | int]]:
    state_machine.set_policy(payload.mode, payload.overrides)
    return {"message": "policy-updated", "mode": payload.mode, "overrides": payload.overrides}


@router.post("/override")
async def overrides(payload: OverridePayload) -> dict[str, str]:
    state_machine.apply_override(payload.symbol.upper(), payload.dict())
    return {"message": "override-accepted"}
