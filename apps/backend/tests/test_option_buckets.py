from datetime import date

from app.domain.options.buckets import contract_metadata, delta_bucket, dte_bucket, option_bucket
from app.services.baselines import PercentileSnapshot, percentile_rank
from app.services.tile_engine import _liquidity_risk_score


def test_option_bucket_helpers():
    metadata = contract_metadata("O:SPX240621C04500000")
    assert metadata["side"] == "CALL"
    assert metadata["dte"] >= 0
    assert metadata["strike"] == 4500.0
    assert metadata["expiry"]
    assert metadata["root"] == "SPX"
    bucket = option_bucket("SPY", 0.38, metadata["dte"], metadata["side"])
    assert bucket.startswith("SPX:CALL:Delta")
    assert delta_bucket(0.35) == "Delta[0.30-0.40]"
    assert dte_bucket(10) == "DTE[7-14]"


def test_percentile_rank_and_liquidity_score():
    baseline = PercentileSnapshot(p50=5, p75=7, p90=9, p95=11, asof=date.today())
    rank = percentile_rank(8, baseline)
    assert 0.75 <= rank <= 0.9
    options = {
        "spread_percentile_rank": rank,
        "flicker_percentile_rank": 0.8,
        "ivr": 45,
        "oi": 15000,
        "spread_pct": 6,
        "nbbo": "stable",
    }
    score = _liquidity_risk_score(options)
    assert 0 <= score <= 100
