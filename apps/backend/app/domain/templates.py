from __future__ import annotations

REGIME_TEMPLATES = {
    "Calm": {"debounce": (5, 8), "spread_ceiling": 6},
    "Normal": {"debounce": (8, 12), "spread_ceiling": 8},
    "Fast": {"debounce": (12, 20), "spread_ceiling": 12},
}

ADMIN_MODES = {
    "Conservative": 0.9,
    "Standard": 1.0,
    "Aggressive": 1.1,
}


def get_template(regime: str, mode: str = "Standard") -> dict:
    template = dict(REGIME_TEMPLATES.get(regime, REGIME_TEMPLATES["Normal"]))
    template["modifier"] = ADMIN_MODES.get(mode, 1)
    return template
