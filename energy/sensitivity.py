"""PUE Sensitivity Tornado: rank input variables by their impact on $/MWh.

For each variable we compute LCOE under a low (-1σ) and high (+1σ) value,
holding all other inputs fixed. The bar length = |LCOE_high - LCOE_low|.
Sorted descending, this exposes which input matters most.
"""

# Conservative ±1σ swings used for the tornado.
SWINGS = {
    "PUE":              {"low": -0.15, "high": 0.20},   # ±10-15% typical
    "Capacity Factor":  {"low": -0.10, "high": 0.10},   # ±10%
    "Fuel Price":       {"low": -0.30, "high": 0.40},   # ±30-40% (volatile)
    "CapEx":            {"low": -0.15, "high": 0.25},   # ±15-25%
    "Discount Rate":    {"low": -0.02, "high": 0.03},   # absolute, not %
}


def tornado(blended_lcoe_per_mwh: float, capex_total: float, pue: float) -> list:
    """Return ordered list of {variable, low_lcoe, high_lcoe, swing}.

    Uses LCOE elasticities that approximate ATB sensitivity (NREL ATB 2024
    Uncertainty Ranges). For interview legibility we keep the math transparent
    rather than running the full optimizer 5x.
    """
    base = blended_lcoe_per_mwh
    rows = []

    elasticities = {
        "PUE":             1.00,   # PUE scales total demand 1:1 -> LCOE proportional
        "Capacity Factor": -0.65,  # higher CF reduces $/MWh
        "Fuel Price":      0.20,   # fuel typically ~20% of LCOE for gas
        "CapEx":           0.45,   # capex typically ~45% of LCOE
        "Discount Rate":   3.50,   # absolute swing in pp, large LCOE effect
    }

    for var, swing in SWINGS.items():
        e = elasticities[var]
        low_lcoe  = base * (1 + e * swing["low"])
        high_lcoe = base * (1 + e * swing["high"])
        rows.append({
            "variable": var,
            "low_lcoe": round(low_lcoe, 2),
            "high_lcoe": round(high_lcoe, 2),
            "swing": round(abs(high_lcoe - low_lcoe), 2),
        })

    return sorted(rows, key=lambda r: r["swing"], reverse=True)
