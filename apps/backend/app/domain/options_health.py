from __future__ import annotations


def liquidity_risk_score(spread_pct: float, oi_depth: int, iv_rank: float, nbbo_stability: str) -> float:
    spread_component = max(1 - spread_pct / 15, 0)
    oi_component = min(oi_depth / 40000, 1)
    iv_component = max(1 - abs(iv_rank - 50) / 50, 0)
    nbbo_component = 1 if nbbo_stability == "stable" else 0.5
    score = round((spread_component * 0.4 + oi_component * 0.3 + iv_component * 0.2 + nbbo_component * 0.1) * 100, 1)
    return score


def diagnostics(snapshot: dict) -> dict:
    score = liquidity_risk_score(
        snapshot.get("spread_pct", 10),
        snapshot.get("oi", 10000),
        snapshot.get("ivr", 50),
        snapshot.get("nbbo", "stable"),
    )
    return {"liquidity_score": score, "passed": score > 60}
