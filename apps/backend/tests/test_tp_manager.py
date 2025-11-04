from datetime import datetime, timezone

import pytest

from app.services.tp_manager import tp_manager
from app.services.timing import get_timing_context


@pytest.mark.asyncio
async def test_tp_manager_snaps_levels_and_updates_hits():
    await tp_manager.reset()
    await tp_manager.update_context(
        "SPY",
        {
            "levels": [
                {"label": "Premarket High", "price": 450.0},
                {"label": "Prior High", "price": 448.5},
            ],
            "atr": 1.5,
            "ema": 447.5,
            "last_price": 447.0,
        },
    )
    timing = get_timing_context(datetime.now(timezone.utc))
    plan = await tp_manager.start(
        "SPY",
        entry=447.0,
        direction="long",
        regime="Normal",
        liquidity_risk=40,
        minute_thrust=0.8,
        divergence=0.2,
        timing=timing,
    )
    assert plan["tp1"]["snapped_to"] in {"Prior High", "Premarket High"}
    updated = await tp_manager.on_tick(
        "SPY",
        price=450.5,
        probability=0.82,
        liquidity_risk=40,
        market_micro={"minuteThrust": 0.9, "divergenceZ": 0.2},
        timing=timing,
    )
    assert updated["tp1"]["hit"], "TP1 should be marked hit once price moves through"
    await tp_manager.stop("SPY")
