from app.domain.scoring.probability import aggregate_probability


def test_probabilities_respect_penalties():
    contributions = {"TrendStack": 0.8, "Levels": 0.7, "Patience": 0.6, "ORB": 0.5, "Market": 0.6, "Options": 0.5}
    penalties = {"chop": -10, "breadth": -5}
    bonuses = {"king": 8}
    probability, band = aggregate_probability(contributions, penalties, bonuses)
    assert 0 <= probability <= 0.99
    assert band.label in {"Loading", "Armed", "EntryReady"}
