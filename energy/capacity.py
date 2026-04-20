"""Capacity-factor lookups per technology and RTO (EIA 860/923).

A capacity factor (CF) is the fraction of a year a plant actually produces
power vs its theoretical max. 8760 hours/year * CF = actual operating hours.
"""

# Sensible industry defaults used if a (tech, rto) pair is missing from data.
DEFAULT_CF = {
    "solar": 0.25,
    "wind": 0.35,
    "geothermal": 0.90,
    "natural_gas": 0.55,
    "coal": 0.50,
    "diesel": 0.05,
    "bess": 0.20,
}


def get_cf(tech: str, rto: str, eia_data: dict) -> float:
    """Return capacity factor for (tech, rto), falling back to a default.

    eia_data shape: {"solar": {"ERCOT": 0.28, "PJM": 0.22, ...}, ...}
    """
    tech_row = eia_data.get(tech, {})
    if rto in tech_row:
        return tech_row[rto]
    return DEFAULT_CF.get(tech, 0.30)
