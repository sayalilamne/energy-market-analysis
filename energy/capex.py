"""Total upfront CapEx ($) for a chosen mix at a given data-center size."""

KW_PER_MW = 1000


def total_capex(mix_pct: dict, size_mw: float, atb_data: dict, premium: float = 1.0) -> float:
    """Sum of (mix_share * size_MW * 1000 kW/MW * $/kW), times resilience premium.

    The optional `premium` multiplier captures the extra CapEx incurred by
    partial-island resilience modes (longer backup duration → bigger BESS,
    redundant gen, switchgear). Default 1.0 = grid-tied baseline.
    """
    total = 0.0
    for tech, pct in mix_pct.items():
        row = atb_data.get(tech, {})
        capex_per_kw = row.get("capex_per_kw", 0.0)
        total += pct * size_mw * KW_PER_MW * capex_per_kw
    return round(total * premium, 0)


def capex_breakdown_by_tech(mix_pct: dict, size_mw: float, atb_data: dict,
                            components: dict, premium: float = 1.0) -> list:
    """Per-tech CapEx split into land/equipment/EPC/interconnection/financing.

    Used by the CapEx Build-Up stacked-bar chart. `components` maps tech ->
    {land, equipment, epc, interconnection, financing} fractions summing to 1.
    Returns one row per tech with USD totals per bucket.
    """
    rows = []
    buckets = ["land", "equipment", "epc", "interconnection", "financing"]
    for tech, pct in mix_pct.items():
        row = atb_data.get(tech, {})
        capex_per_kw = row.get("capex_per_kw", 0.0)
        tech_total = pct * size_mw * KW_PER_MW * capex_per_kw * premium
        split = components.get(tech, {})
        rows.append({
            "tech": tech,
            "total": round(tech_total, 0),
            **{b: round(tech_total * split.get(b, 0.0), 0) for b in buckets},
        })
    return rows
