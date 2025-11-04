from app.domain.what_if import evaluate_what_if


def test_what_if_bonus_effect():
    result = evaluate_what_if("SPY", {"orbRetestConfirms": True, "spreadShrinksTo": 5})
    assert result.band.label in {"Armed", "EntryReady"}
    assert 0 <= result.probability <= 0.99
