import pytest

from energy.optimizer import run_analysis


BASE = {
    "primary_goal": "Balanced",
    "reliability": "Standard (99.9%)",
    "carbon_goal": "No mandate",
    "geography": "Mid-Atlantic",
    "primary_workload": "AI-Training",
    "speed_to_power": "2-5 years",
    "cost_priority": "Balanced",
    "rto": "PJM",
    "size_mw": 250,
    "type": "Hyperscale",
    "ppa": "virtual",
}


REQUIRED_KEYS = {
    "mix_pct", "blended_lcoe_per_mwh", "total_capex_usd",
    "carbon_free_score", "feasibility", "emissions", "recommendations", "tooltips",
}


def test_balanced_pjm_full_result_shape():
    res = run_analysis(BASE)
    assert REQUIRED_KEYS.issubset(res.keys())
    assert abs(sum(res["mix_pct"].values()) - 1.0) < 0.01
    assert res["blended_lcoe_per_mwh"] > 0
    assert res["total_capex_usd"] > 0
    assert len(res["recommendations"]) == 5


@pytest.mark.parametrize("goal", ["Cost", "Carbon", "Reliability", "Balanced"])
def test_all_primary_goals_produce_valid_mix(goal):
    inputs = {**BASE, "primary_goal": goal}
    res = run_analysis(inputs)
    assert abs(sum(res["mix_pct"].values()) - 1.0) < 0.01


def test_247_cfe_removes_fossil_techs():
    inputs = {**BASE, "primary_goal": "Balanced", "carbon_goal": "24/7 Carbon-free"}
    res = run_analysis(inputs)
    assert "natural_gas" not in res["mix_pct"]
    assert "diesel" not in res["mix_pct"]
    assert "coal" not in res["mix_pct"]


def test_carbon_goal_improves_cfe_score():
    low = run_analysis({**BASE, "primary_goal": "Cost", "carbon_goal": "No mandate"})
    high = run_analysis({**BASE, "primary_goal": "Carbon", "carbon_goal": "24/7 Carbon-free"})
    assert high["carbon_free_score"] > low["carbon_free_score"]
