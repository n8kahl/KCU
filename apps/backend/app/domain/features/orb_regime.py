from __future__ import annotations


def orb_regime_score(range_pct_adr: float, acceptance_time: float, retest_success: bool) -> dict:
    range_score = max(1 - abs(range_pct_adr - 0.3), 0)
    acceptance_score = min(acceptance_time / 600, 1)
    retest_bonus = 0.2 if retest_success else 0
    score = round(min(range_score * 0.5 + acceptance_score * 0.3 + retest_bonus, 1), 3)
    return {
        "score": score,
        "reasons": [
            f"range: {range_score:.2f}",
            f"acceptance: {acceptance_score:.2f}",
            f"retest: {'yes' if retest_success else 'no'}",
        ],
    }
