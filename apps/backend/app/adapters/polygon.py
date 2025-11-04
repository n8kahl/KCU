from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.core.settings import settings

BASE_URL = "https://api.polygon.io"


class PolygonClient:
    def __init__(self) -> None:
        if not settings.polygon_api_key:
            raise RuntimeError("Polygon API key required")
        self._client = httpx.AsyncClient(base_url=BASE_URL, timeout=10)

    async def __aenter__(self) -> "PolygonClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        params = params or {}
        params["apiKey"] = settings.polygon_api_key
        response = await self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def get_aggregates(self, ticker: str, tf: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        payload = await self._get(
            f"/v2/aggs/ticker/{ticker}/range/1/{tf}/{int(start.timestamp()*1000)}/{int(end.timestamp()*1000)}"
        )
        return payload.get("results", [])

    async def get_previous_close(self, ticker: str) -> dict[str, Any]:
        return await self._get(f"/v2/aggs/ticker/{ticker}/prev")

    async def get_premarket_range(self, ticker: str, date_: datetime) -> dict[str, Any]:
        return await self._get(f"/v1/open-close/{ticker}/{date_.date()}")

    async def get_quote_snapshot(self, ticker: str) -> dict[str, Any]:
        data = await self._get(f"/v2/snapshot/ticker/{ticker}")
        bid = data.get("bid", {}).get("p", 0)
        ask = data.get("ask", {}).get("p", 0)
        mid = (bid + ask) / 2 if (bid and ask) else 0
        spread_pct = round(((ask - bid) / mid) * 100, 3) if mid else None
        quote = data.get("quote", {})
        status = quote.get("conditionCode", "stable")
        return {
            "bid": bid,
            "ask": ask,
            "mid": mid,
            "nbbo_quality": status,
            "spread_pct_of_mid": spread_pct,
        }

    async def get_options_chain(self, ticker: str, date_: datetime) -> list[dict[str, Any]]:
        payload = await self._get(f"/v3/snapshot/options/{ticker}", params={"expiration_date": date_.date()})
        contracts = []
        for item in payload.get("results", []):
            contract = item.get("details", {}).get("contract_name")
            greeks = item.get("greeks", {})
            last_quote = item.get("last_quote", {})
            bid = last_quote.get("bid", 0)
            ask = last_quote.get("ask", 0)
            mid = (bid + ask) / 2 if bid and ask else 0
            spread_pct = round(((ask - bid) / mid) * 100, 3) if mid else None
            contracts.append(
                {
                    "contract": contract,
                    "bid": bid,
                    "ask": ask,
                    "mid": mid,
                    "spread_pct_of_mid": spread_pct,
                    "oi": item.get("open_interest"),
                    "volume": item.get("volume"),
                    "iv": item.get("implied_volatility"),
                    "delta": greeks.get("delta"),
                    "theta": greeks.get("theta"),
                }
            )
        return contracts

    async def close(self) -> None:
        await self._client.aclose()
