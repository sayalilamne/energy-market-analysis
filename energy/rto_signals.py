"""24/7 Carbon-Free Energy (CFE) matching score from pre-fetched RTO data.

Hourly-matching score = fraction of hours where on-site CFE supply meets load.
Uses snapshots produced offline by scripts/fetch_rto_gridstatus.py.
"""


def cfe_score(mix_pct: dict, rto: str, hourly_data: dict) -> float:
    """Rough 24/7 CFE score on a 0-100 scale.

    Heuristic for v1:
      grid_cf_share (avg over the week) + on_site_cfe_share, capped at 1.0,
      then scaled to 0-100.

    hourly_data shape: {"ERCOT": {"avg_cf_share": 0.32}, ...}
    """
    grid = hourly_data.get(rto, {}).get("avg_cf_share", 0.0)
    on_site = sum(
        pct for tech, pct in mix_pct.items()
        if tech in {"solar", "wind", "geothermal", "nuclear"}
    )
    combined = min(1.0, grid * 0.3 + on_site * 0.7)
    return round(combined * 100, 1)
