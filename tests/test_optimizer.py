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
    "grid_relationship": "Grid-tied, mixed fleet",
    "resilience": "Non-island",
    "duration": "n/a",
    "pue": 1.4,
}


REQUIRED_KEYS = {
    "mix_pct", "blended_lcoe_per_mwh", "lcoe_post_ira", "lcoe_components",
    "total_capex_usd", "capex_breakdown", "feasibility", "emissions",
    "iea_nze", "duck_curve", "sensitivity",
    "recommendations", "tooltips",
}


def test_balanced_pjm_full_result_shape():
    res = run_analysis(BASE)
    assert REQUIRED_KEYS.issubset(res.keys())
    assert abs(sum(res["mix_pct"].values()) - 1.0) < 0.01
    assert res["blended_lcoe_per_mwh"] > 0
    assert res["total_capex_usd"] > 0
    assert len(res["recommendations"]) == 5
    # New outputs:
    assert "scope1_tons" in res["emissions"]
    assert res["lcoe_post_ira"] <= res["blended_lcoe_per_mwh"]
    assert len(res["sensitivity"]) == 5


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


def test_pue_scales_capex_and_emissions():
    low  = run_analysis({**BASE, "pue": 1.1})
    high = run_analysis({**BASE, "pue": 2.5})
    assert high["total_capex_usd"] > low["total_capex_usd"]
    assert high["emissions"]["location_tons"] > low["emissions"]["location_tons"]


def test_partial_island_adds_capex_premium():
    base = run_analysis(BASE)
    island = run_analysis({**BASE, "resilience": "Partial island", "duration": "72 hr+"})
    assert island["total_capex_usd"] > base["total_capex_usd"]
    assert island["premium"] > 1.0


def test_grid_relationship_re_storage_drops_fossils():
    res = run_analysis({**BASE, "grid_relationship": "Grid-tied, RE + storage"})
    assert "coal" not in res["mix_pct"]
    assert "diesel" not in res["mix_pct"]
