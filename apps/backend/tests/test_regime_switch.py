from app.domain.regimes import detect_regime


def test_regime_switch_fast():
    assert detect_regime(0.9, 0.7, 0.6, 0.5) == "Fast"


def test_regime_switch_calm():
    assert detect_regime(0.1, 0.1, 0.2, 0.1) == "Calm"
