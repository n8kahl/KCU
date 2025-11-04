from __future__ import annotations


def levels_cluster(distance_to_level: float, orb_overlap: float, anchored_vwap_dist: float) -> dict:
    proximity_score = max(1 - abs(distance_to_level) / 2, 0)
    orb_score = max(1 - orb_overlap, 0)
    vwap_score = max(1 - abs(anchored_vwap_dist) / 1.5, 0)
    score = round((proximity_score + orb_score + vwap_score) / 3, 3)
    return {
        "score": score,
        "reasons": [
            f"level proximity: {proximity_score:.2f}",
            f"orb overlap: {orb_score:.2f}",
            f"vwap dist: {vwap_score:.2f}",
        ],
    }
