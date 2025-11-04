from __future__ import annotations

from typing import List


def rank_contracts(contracts: List[dict], delta_range: tuple[float, float], spread_ceiling: float) -> list[dict]:
    ranked = []
    low, high = delta_range
    for contract in contracts:
        delta = abs(contract.get("delta", 0))
        spread = contract.get("spread_pct_of_mid") or 999
        if not (low <= delta <= high):
            continue
        if spread > spread_ceiling:
            continue
        ranked.append((spread, contract.get("mid", 0), contract))
    ranked.sort(key=lambda x: (x[0], -x[1]))
    return [item[2] for item in ranked[:3]]
