from energy.lcoe import blended_lcoe, capital_recovery_factor, tech_lcoe


ATB = {
    "solar": {"capex_per_kw": 1200, "fixed_om": 18, "variable_om": 0, "fuel_cost": 0, "lifetime": 30},
    "natural_gas": {"capex_per_kw": 1100, "fixed_om": 15, "variable_om": 2.5, "fuel_cost": 28, "lifetime": 30},
}
EIA = {"solar": {"PJM": 0.22}, "natural_gas": {"PJM": 0.55}}


def test_crf_matches_textbook():
    # r=7%, n=30 -> CRF ≈ 0.0806
    assert round(capital_recovery_factor(0.07, 30), 4) == 0.0806


def test_solar_lcoe_positive():
    lcoe = tech_lcoe("solar", "PJM", ATB, EIA)
    assert 40 < lcoe < 120  # sane $/MWh range


def test_blended_is_weighted_average():
    mix = {"solar": 0.5, "natural_gas": 0.5}
    blended = blended_lcoe(mix, "PJM", ATB, EIA)
    solar = tech_lcoe("solar", "PJM", ATB, EIA)
    gas = tech_lcoe("natural_gas", "PJM", ATB, EIA)
    assert abs(blended - 0.5 * (solar + gas)) < 0.02
