"""IRA (Inflation Reduction Act) incentive modeling.

Two mechanisms in the Act for clean-power generation:
  - ITC (Investment Tax Credit): one-time CapEx reduction (e.g. 30% for solar).
  - PTC (Production Tax Credit): per-MWh credit over 10 yrs (e.g. $27.5 for wind).

For LCOE we levelize both onto a $/MWh basis so they're comparable.
"""

from .lcoe import capital_recovery_factor, DISCOUNT_RATE, HOURS_PER_YEAR
from .capacity import get_cf


def ira_credit_per_mwh(tech: str, rto: str, atb_data: dict, eia_data: dict, ira_data: dict) -> float:
    """Levelized IRA credit value in $/MWh for a given tech."""
    incentive = ira_data.get(tech, {})
    if incentive.get("type") == "PTC":
        return incentive.get("ptc_per_mwh", 0.0)

    if incentive.get("type") == "ITC":
        atb_row = atb_data.get(tech, {})
        if not atb_row:
            return 0.0
        cf = get_cf(tech, rto, eia_data)
        if cf <= 0:
            return 0.0
        crf = capital_recovery_factor(DISCOUNT_RATE, atb_row["lifetime"])
        capex_per_kw = atb_row["capex_per_kw"]
        # ITC reduces effective CapEx by itc_pct -> CapEx-related $/MWh saved.
        savings_per_kw_yr = crf * capex_per_kw * incentive["itc_pct"]
        return savings_per_kw_yr / (HOURS_PER_YEAR * cf / 1000)

    return 0.0


def lcoe_with_ira(blended_lcoe: float, mix_pct: dict, rto: str,
                  atb_data: dict, eia_data: dict, ira_data: dict) -> float:
    """Blended LCOE after subtracting weighted IRA credits."""
    credit = sum(
        pct * ira_credit_per_mwh(tech, rto, atb_data, eia_data, ira_data)
        for tech, pct in mix_pct.items()
    )
    return round(max(blended_lcoe - credit, 0), 2)
