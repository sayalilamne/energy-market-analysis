"""Blended Levelized Cost of Energy (LCOE) — NREL ATB 2024 based.

Formula per technology (simplified):
    LCOE = (CRF * CapEx_per_kW + Fixed_OM_per_kW) / (8760 * CF)
           + Variable_OM_per_MWh + Fuel_per_MWh

Where CRF (capital recovery factor) = r * (1+r)^n / ((1+r)^n - 1)
    r = discount rate (decimal), n = lifetime in years

The *blended* LCOE across a mix is the sum of (mix_pct_i * LCOE_i).
"""

from .capacity import get_cf

HOURS_PER_YEAR = 8760
DISCOUNT_RATE = 0.07  # Common NREL ATB assumption


def capital_recovery_factor(rate: float, lifetime_years: int) -> float:
    """CRF spreads upfront CapEx over plant lifetime as an annual payment."""
    if rate == 0:
        return 1 / lifetime_years
    factor = (1 + rate) ** lifetime_years
    return rate * factor / (factor - 1)


def tech_lcoe(tech: str, rto: str, atb_data: dict, eia_data: dict) -> float:
    """LCOE in $/MWh for one technology in one RTO."""
    row = atb_data.get(tech, {})
    if not row:
        return 0.0

    cf = get_cf(tech, rto, eia_data)
    if cf <= 0:
        return 0.0

    crf = capital_recovery_factor(DISCOUNT_RATE, row["lifetime"])
    capex_per_kw = row["capex_per_kw"]
    fixed_om = row["fixed_om"]  # $/kW-year
    variable_om = row["variable_om"]  # $/MWh
    fuel = row.get("fuel_cost", 0.0)  # $/MWh

    # $/MWh = ($/kW-year) / (MWh/kW-year) = ($/kW-year) / (8760 * CF / 1000)
    fixed_per_mwh = (crf * capex_per_kw + fixed_om) / (HOURS_PER_YEAR * cf / 1000)
    return fixed_per_mwh + variable_om + fuel


def blended_lcoe(mix_pct: dict, rto: str, atb_data: dict, eia_data: dict) -> float:
    """Weighted-average LCOE across a mix. mix_pct values should sum to 1.0."""
    total = 0.0
    for tech, pct in mix_pct.items():
        total += pct * tech_lcoe(tech, rto, atb_data, eia_data)
    return round(total, 2)
