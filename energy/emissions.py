"""Carbon emissions: Scope 1 (on-site combustion) + Scope 2 (purchased grid).

Scope 1 (GHG Protocol Corporate Standard, 2015):
    On-site fuel combustion only — gas turbines, diesel generators, coal.
    = Σ (mix_share_i × annual_MWh × scope1_factor_i) for fossil techs

Scope 2 (GHG Protocol Scope 2 Guidance, 2015):
    Location-based: grid average × Annual_MWh
    Market-based:   (1 − carbon_free_share) × Location-based

Units: metric tons CO2-equivalent per year.
"""

LB_PER_METRIC_TON = 2204.62
HOURS_PER_YEAR = 8760

CARBON_FREE_TECHS = {"solar", "wind", "geothermal", "hydro", "nuclear", "bess"}


def carbon_free_share(mix_pct: dict) -> float:
    """Fraction of the mix that is carbon-free at the source."""
    return sum(pct for tech, pct in mix_pct.items() if tech in CARBON_FREE_TECHS)


def scope1(mix_pct: dict, size_mw: float, scope1_factors: dict) -> float:
    """Tons CO2e/yr from on-site fuel combustion (gas/diesel/coal generation)."""
    annual_mwh = size_mw * HOURS_PER_YEAR
    total_lb = 0.0
    for tech, pct in mix_pct.items():
        factor = scope1_factors.get(tech, 0)
        total_lb += pct * annual_mwh * factor
    return round(total_lb / LB_PER_METRIC_TON, 0)


def scope2(mix_pct: dict, rto: str, size_mw: float, egrid_data: dict) -> dict:
    """Return location- & market-based Scope 2 in metric tons CO2e."""
    intensity_lb_per_mwh = egrid_data.get(rto, egrid_data.get("_default", 900.0))
    annual_mwh = size_mw * HOURS_PER_YEAR

    location_lb = intensity_lb_per_mwh * annual_mwh
    cf_share = carbon_free_share(mix_pct)
    market_lb = (1 - cf_share) * location_lb

    return {
        "location_tons": round(location_lb / LB_PER_METRIC_TON, 0),
        "market_tons":   round(market_lb / LB_PER_METRIC_TON, 0),
        "cf_share":      round(cf_share, 3),
        "intensity_lb_per_mwh": intensity_lb_per_mwh,
    }
