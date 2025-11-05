from __future__ import annotations

import re
from datetime import datetime, timezone

ETF_INDEX = {
    "SPY": "SPX",
    "QQQ": "NDX",
}


CONTRACT_REGEX = re.compile(
    r"^(?P<root>[A-Z]+)(?P<expiry>\d{6})(?P<type>[CP])(?P<strike>\d{8})(?P<suffix>.*)?$"
)


def contract_metadata(contract: str | None) -> dict:
    if not contract:
        return {"side": None, "dte": None, "strike": None, "expiry": None, "root": None}
    payload = contract.replace("O:", "")
    match = CONTRACT_REGEX.match(payload)
    expiry = None
    side = None
    strike = None
    root = None
    if match:
        root = match.group("root")
        expiry_token = match.group("expiry")
        try:
            expiry = datetime.strptime(expiry_token, "%y%m%d").date()
        except ValueError:
            expiry = None
        side = "CALL" if match.group("type") == "C" else "PUT"
        strike_token = match.group("strike")
        try:
            strike = int(strike_token) / 1000
        except ValueError:
            strike = None
    else:
        side = "CALL" if "C" in payload else ("PUT" if "P" in payload else None)
    dte = None
    expiry_iso = None
    if expiry:
        dte = max((expiry - datetime.now(timezone.utc).date()).days, 0)
        expiry_iso = expiry.isoformat()
    return {"side": side, "dte": dte, "strike": strike, "expiry": expiry_iso, "root": root}


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
