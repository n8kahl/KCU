from app.domain.options_health import diagnostics


def test_options_health_pass_fail():
    healthy = diagnostics({"spread_pct": 4, "oi": 40000, "ivr": 40, "nbbo": "stable"})
    risky = diagnostics({"spread_pct": 20, "oi": 2000, "ivr": 80, "nbbo": "crossed"})
    assert healthy["passed"] is True
    assert risky["passed"] is False
