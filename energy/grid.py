"""Grid-relationship adjustments: reshape mix per user's grid strategy."""


GRID_RELATIONSHIPS = {
    "Grid-tied, RE + storage": {
        "boost":  ["solar", "wind", "bess", "hydro"],
        "remove": ["coal", "diesel"],
    },
    "Grid-tied, mixed fleet": {
        "boost":  [],
        "remove": [],
    },
    "Grid-tied, gas bridge": {
        "boost":  ["natural_gas", "bess"],
        "remove": ["coal"],
    },
}


def apply_grid_relationship(mix_pct: dict, relationship: str) -> dict:
    """Lift boosted techs by 30% relative; remove banned techs; renormalize."""
    cfg = GRID_RELATIONSHIPS.get(relationship)
    if not cfg:
        return mix_pct

    out = {k: v for k, v in mix_pct.items() if k not in cfg["remove"]}
    for tech in cfg["boost"]:
        if tech in out:
            out[tech] *= 1.3
    total = sum(out.values())
    if total == 0:
        return mix_pct
    return {k: round(v / total, 3) for k, v in out.items()}
