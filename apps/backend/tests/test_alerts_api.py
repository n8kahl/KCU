import pytest
from httpx import AsyncClient

from app.core.settings import settings
from app.main import app


@pytest.mark.asyncio
async def test_alert_endpoint_sends_discord(monkeypatch) -> None:
    captured: dict[str, str] = {}

    async def fake_send(webhook: str | None, content: str) -> None:
        captured["webhook"] = webhook or ""
        captured["content"] = content

    monkeypatch.setattr("app.api.alerts.send_alert", fake_send)
    original = settings.discord_webhook_url
    settings.discord_webhook_url = "https://discord.test/hook"
    payload = {
        "action": "enter",
        "symbol": "SPY",
        "contract": "O:SPY240621C00450000",
        "price": 1.23,
        "grade": "A",
        "confidence": 92,
        "level": "Premarket High",
        "stop": 448.0,
        "target": 455.0,
        "note": "Testing hook",
    }
    try:
        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post("/api/alerts", json=payload)
        assert resp.status_code == 200
        assert captured["webhook"] == "https://discord.test/hook"
        assert "SPY" in captured["content"]
        assert "[Enter]" in captured["content"]
    finally:
        settings.discord_webhook_url = original


@pytest.mark.asyncio
async def test_alert_validation() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/alerts",
            json={
                "action": "enter",
                "symbol": "",
                "contract": "O:SPY240621C00450000",
                "price": 0,
                "grade": "A",
                "confidence": 101,
                "level": "",
                "stop": 0,
                "target": 0,
            },
        )
    assert resp.status_code == 422
