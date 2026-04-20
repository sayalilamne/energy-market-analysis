from energy.feasibility import feasibility_flag


def test_pjm_under_2_years_infeasible():
    inputs = {"rto": "PJM", "speed_to_power": "<2 years"}
    res = feasibility_flag(inputs)
    assert res["flag"] == "Not Feasible"
    assert "PJM" in res["reason"]


def test_ercot_under_2_years_feasible():
    inputs = {"rto": "ERCOT", "speed_to_power": "<2 years"}
    assert feasibility_flag(inputs)["flag"] == "Feasible"


def test_long_horizon_always_feasible():
    for rto in ["CAISO", "ERCOT", "PJM", "NYISO", "MISO", "SPP", "ISO-NE"]:
        inputs = {"rto": rto, "speed_to_power": "5+ years"}
        assert feasibility_flag(inputs)["flag"] == "Feasible"
