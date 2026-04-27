"""Resilience-mode adjustments: backup sizing and CapEx premium.

Island mode means the data center can run disconnected from the grid for some
duration. Longer durations require more storage + on-site firm generation,
which adds CapEx vs a non-island baseline.
"""

# CapEx premium (multiplier on baseline) per (resilience, duration) cell.
# Baseline = Non-island (1.00x).
PREMIUM = {
    ("Non-island", "n/a"):       1.00,
    ("Partial island", "4 hr"):  1.10,
    ("Partial island", "24 hr"): 1.22,
    ("Partial island", "72 hr+"):1.40,
}

# Storage MW required as fraction of site size, by duration.
STORAGE_FRACTION = {
    "n/a":    0.05,
    "4 hr":   0.20,
    "24 hr":  0.40,
    "72 hr+": 0.65,
}


def apply_resilience(mix_pct: dict, resilience: str, duration: str) -> dict:
    """Increase BESS share for partial-island modes; rebalance other techs proportionally."""
    target_bess = STORAGE_FRACTION.get(duration, 0.05)
    if mix_pct.get("bess", 0) >= target_bess:
        return mix_pct
    delta = target_bess - mix_pct.get("bess", 0)
    others = {k: v for k, v in mix_pct.items() if k != "bess"}
    other_total = sum(others.values())
    if other_total == 0:
        return mix_pct
    scale = (other_total - delta) / other_total
    new_mix = {k: round(v * scale, 3) for k, v in others.items()}
    new_mix["bess"] = round(target_bess, 3)
    return new_mix


def capex_premium(resilience: str, duration: str) -> float:
    """Multiplier applied to baseline CapEx for the chosen resilience setting."""
    return PREMIUM.get((resilience, duration), 1.00)


def premium_matrix() -> list:
    """3x3 matrix used by the Island Mode Duration heatmap (Chart 9).

    Returns list of {mode, duration, premium_pct, storage_mw_per_mw}.
    """
    rows = []
    for (mode, dur), prem in PREMIUM.items():
        rows.append({
            "mode": mode,
            "duration": dur,
            "premium_pct": round((prem - 1) * 100, 1),
            "storage_fraction": STORAGE_FRACTION.get(dur, 0.05),
        })
    return rows
