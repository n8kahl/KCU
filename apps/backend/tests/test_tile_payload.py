import pytest
from httpx import AsyncClient

from app.core.settings import settings
from app.main import app
from app.services.state_store import state_store


@pytest.mark.asyncio
async def test_tile_state_contains_visual_fields() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/tickers", json={"ticker": "XYZ"})
        resp = await client.get("/api/tickers/XYZ/state")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["grade"]
    assert isinstance(payload["bars"], list)
    assert isinstance(payload["ema8"], list)
    assert "delta_to_entry" in payload
    assert "key_levels" in payload
    assert "options_top3" in payload


@pytest.mark.asyncio
async def test_options_flag_controls_top3() -> None:
    original = settings.options_data_enabled
    settings.options_data_enabled = False
    try:
        state_store._states.clear()
        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.get("/api/tickers/SPY/state")
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["options_top3"] == []
    finally:
        settings.options_data_enabled = original
