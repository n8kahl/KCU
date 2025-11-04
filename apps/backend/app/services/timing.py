from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

WINDOWS = [
    {
        "name": "Opening Drive",
        "start": time(9, 30),
        "end": time(9, 45),
        "tf_primary": "2m",
        "tf_backup": "1m/5m",
        "kcu_mode": "Opening Drive",
        "considerations": [
            "ORB still forming",
            "Spreads wider, patience strict",
        ],
    },
    {
        "name": "Morning Trend",
        "start": time(9, 45),
        "end": time(11, 30),
        "tf_primary": "5m",
        "tf_backup": "2m/10m",
        "kcu_mode": "Standard",
        "considerations": [
            "K&Q reliable",
            "Watch VWAP retests",
        ],
    },
    {
        "name": "Midday Compression",
        "start": time(11, 30),
        "end": time(13, 0),
        "tf_primary": "10m",
        "tf_backup": "5m",
        "kcu_mode": "Standard Midday",
        "considerations": [
            "Lower targets",
            "Expect chop & divergence",
        ],
    },
    {
        "name": "Afternoon Cloud",
        "start": time(13, 0),
        "end": time(15, 15),
        "tf_primary": "5m/10m",
        "tf_backup": "2m",
        "kcu_mode": "Cloud Eligible",
        "considerations": [
            "Cloud runner allowed",
            "Monitor liquidity",
        ],
    },
    {
        "name": "Late Day",
        "start": time(15, 15),
        "end": time(16, 0),
        "tf_primary": "2m/5m",
        "tf_backup": "1m",
        "kcu_mode": "Power Hour",
        "considerations": [
            "Micro spikes common",
            "Tighten trail",
        ],
    },
]


def get_timing_context(now_utc: datetime) -> dict:
    eastern = now_utc.astimezone(ZoneInfo("US/Eastern"))
    current_time = eastern.time()
    window = WINDOWS[-1]
    for candidate in WINDOWS:
        if candidate["start"] <= current_time < candidate["end"]:
            window = candidate
            break
    label = f"{eastern.strftime('%H:%M')} ET · KCU: {window['name']}"
    return {
        "label": label,
        "window": window["name"],
        "tf_primary": window["tf_primary"],
        "tf_backup": window["tf_backup"],
        "kcu_mode": window["kcu_mode"],
        "considerations": window["considerations"],
    }
