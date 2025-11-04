from app.domain.contract_picker import rank_contracts


def test_contract_picker_spread_ceiling():
    contracts = [
        {"contract": "A", "delta": 0.4, "spread_pct_of_mid": 5, "mid": 2.0},
        {"contract": "B", "delta": 0.42, "spread_pct_of_mid": 15, "mid": 1.0},
        {"contract": "C", "delta": 0.5, "spread_pct_of_mid": 6, "mid": 1.5},
    ]
    ranked = rank_contracts(contracts, (0.35, 0.55), 8)
    assert [r["contract"] for r in ranked] == ["A", "C"]
