import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_watchlist_crud() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/tickers")
        assert resp.status_code == 200
        baseline = resp.json()["tickers"]
        assert isinstance(baseline, list)

        resp = await client.post("/api/tickers", json={"ticker": "AMD"})
        assert resp.status_code == 200
        assert "AMD" in resp.json()["tickers"]

        state_resp = await client.get("/api/tickers/AMD/state")
        assert state_resp.status_code == 200
        assert state_resp.json()["symbol"] == "AMD"

        resp = await client.delete("/api/tickers/AMD")
        assert resp.status_code == 200
        assert "AMD" not in resp.json()["tickers"]
