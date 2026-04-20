"""Total upfront CapEx ($) for a chosen mix at a given data-center size."""

KW_PER_MW = 1000


def total_capex(mix_pct: dict, size_mw: float, atb_data: dict) -> float:
    """Sum of (mix_share * size_MW * 1000 kW/MW * $/kW) across all techs."""
    total = 0.0
    for tech, pct in mix_pct.items():
        row = atb_data.get(tech, {})
        capex_per_kw = row.get("capex_per_kw", 0.0)
        total += pct * size_mw * KW_PER_MW * capex_per_kw
    return round(total, 0)
