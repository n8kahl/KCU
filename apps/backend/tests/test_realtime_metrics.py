import pytest

from app.domain.features.microstructure import divergence_z, micro_chop, minute_thrust
from app.domain.types import ProbabilityBand, TileState
import app.services.rings as rings
from app.services.state_store import state_store
from app.services.tile_engine import merge_realtime_into_tile


def test_minute_thrust_and_micro_chop_behaviour():
    closes = [100, 101, 102, 101.5, 102.5, 103.5]
    thrust = minute_thrust(closes, lookback=5)
    assert thrust > 0

    one_second_returns = [0.001, -0.001, 0.001, -0.001, 0.0005, -0.0005] * 5
    chop = micro_chop(one_second_returns)
    assert 0 <= chop <= 1

    div = divergence_z([100, 101, 102, 103, 104], [100, 100.5, 101, 101.5, 102])
    assert div != 0


def test_rings_cap_lengths():
    for idx in range(400):
        rings.push_index_value("TESTIDX", idx, float(idx))
    assert len(rings.last_index_1s("TESTIDX", 1000)) <= 300


@pytest.mark.asyncio
async def test_merge_realtime_updates_market_microstructure():
    band = ProbabilityBand.from_score(60)
    tile = TileState(
        symbol="SPY",
        regime="Normal",
        probability_to_action=0.6,
        band=band,
        confidence={"p50": 0.5, "p68": 0.6, "p95": 0.8},
        breakdown=[
            {"name": "TrendStack", "score": 0.6},
            {"name": "Levels", "score": 0.6},
            {"name": "Patience", "score": 0.6},
            {"name": "ORB", "score": 0.6},
            {"name": "Market", "score": 0.5},
            {"name": "Options", "score": 0.5},
        ],
        options={"contracts": {"primary": None, "backups": []}},
        rationale={"positives": [], "risks": []},
        admin={"mode": "Standard", "overrides": {}, "marketMicro": {"minuteThrust": 0, "microChop": 0, "divergenceZ": 0}},
        timestamps={"updated": "now"},
        eta_seconds=None,
        penalties={},
        bonuses={"king_queen": 8},
        history=[],
    )
    await state_store.set_state("SPY", tile)
    updated = await merge_realtime_into_tile(
        "SPY",
        {"marketMicro": {"minuteThrust": 0.8, "microChop": 0.7, "divergenceZ": 1.6}},
    )
    assert updated.penalties["chop"] == -8
    assert "king_queen" in updated.bonuses and updated.bonuses["king_queen"] <= 5
