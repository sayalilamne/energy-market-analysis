"""Scope 2 carbon emissions (location-based and market-based) from EPA eGRID.

Location-based: grid average emissions for the region the site sits in.
    = grid_intensity_lb_per_mwh * annual_mwh

Market-based: accounts for clean-energy procurement (PPAs, on-site CFE).
    = (1 - carbon_free_share) * location_based

Units: pounds of CO2-equivalent per year.
"""

LB_PER_METRIC_TON = 2204.62
HOURS_PER_YEAR = 8760

CARBON_FREE_TECHS = {"solar", "wind", "geothermal", "bess"}


def carbon_free_share(mix_pct: dict) -> float:
    """Fraction of the mix that is carbon-free at the source."""
    return sum(pct for tech, pct in mix_pct.items() if tech in CARBON_FREE_TECHS)


def scope2(mix_pct: dict, rto: str, size_mw: float, egrid_data: dict) -> dict:
    """Return {'location_tons': ..., 'market_tons': ..., 'cf_share': ...}."""
    intensity_lb_per_mwh = egrid_data.get(rto, egrid_data.get("_default", 900.0))
    annual_mwh = size_mw * HOURS_PER_YEAR

    location_lb = intensity_lb_per_mwh * annual_mwh
    cf_share = carbon_free_share(mix_pct)
    market_lb = (1 - cf_share) * location_lb

    return {
        "location_tons": round(location_lb / LB_PER_METRIC_TON, 0),
        "market_tons": round(market_lb / LB_PER_METRIC_TON, 0),
        "cf_share": round(cf_share, 3),
    }
