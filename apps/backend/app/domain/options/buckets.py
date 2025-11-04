from __future__ import annotations

from datetime import datetime, timezone

ETF_INDEX = {
    "SPY": "SPX",
    "QQQ": "NDX",
}


def contract_metadata(contract: str | None) -> dict:
    if not contract:
        return {"side": None, "dte": None}
    payload = contract.replace("O:", "")
    side = "CALL" if "C" in payload else ("PUT" if "P" in payload else None)
    expiry = None
    for idx in range(len(payload) - 5):
        chunk = payload[idx : idx + 6]
        if chunk.isdigit():
            try:
                expiry = datetime.strptime(chunk, "%y%m%d").date()
                break
            except ValueError:
                continue
    dte = None
    if expiry:
        dte = max((expiry - datetime.now(timezone.utc).date()).days, 0)
    return {"side": side, "dte": dte}


def delta_bucket(delta: float | None) -> str:
    if delta is None:
        return "Delta[unknown]"
    floor = round(max(0.0, delta - 0.05), 2)
    ceil = round(min(1.0, floor + 0.1), 2)
    return f"Delta[{floor:.2f}-{ceil:.2f}]"


def dte_bucket(dte: int | None) -> str:
    if dte is None:
        return "DTE[unknown]"
    if dte <= 3:
        return "DTE[0-3]"
    if dte <= 7:
        return "DTE[3-7]"
    if dte <= 14:
        return "DTE[7-14]"
    return "DTE[14+]"


def option_bucket(symbol: str, delta: float | None, dte: int | None, side: str | None) -> str:
    underlying = ETF_INDEX.get(symbol, symbol)
    delta_key = delta_bucket(delta)
    dte_key = dte_bucket(dte)
    side_key = side or "UNKNOWN"
    return f"{underlying}:{side_key}:{delta_key}:{dte_key}"
