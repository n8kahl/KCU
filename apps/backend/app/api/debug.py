from fastapi import APIRouter

from app.services.realtime_engine import _current_subscriptions
from app.services.state_store import state_store

router = APIRouter()


@router.get("/debug/stream")
async def stream_status():
    states = await state_store.all_states()
    return {
        "subscriptions": _current_subscriptions(),
        "symbols": [s.symbol for s in states],
        "count": len(states),
    }
