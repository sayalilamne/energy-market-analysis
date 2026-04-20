from energy.emissions import carbon_free_share, scope2


EGRID = {"PJM": 824.0, "_default": 855.0}


def test_cf_share_counts_only_carbon_free_techs():
    assert carbon_free_share({"solar": 0.4, "wind": 0.3, "natural_gas": 0.3}) == 0.7


def test_market_less_than_location_when_cfe_in_mix():
    all_coal = {"coal": 1.0}
    half_solar = {"coal": 0.5, "solar": 0.5}
    size_mw = 100

    a = scope2(all_coal, "PJM", size_mw, EGRID)
    b = scope2(half_solar, "PJM", size_mw, EGRID)

    assert a["location_tons"] == b["location_tons"]  # same grid intensity
    assert b["market_tons"] < a["market_tons"]        # CFE procurement reduces market


def test_magnitude_reasonable():
    # 100 MW * 8760 hr * 824 lb/MWh ≈ 327k metric tons / year
    result = scope2({"coal": 1.0}, "PJM", 100, EGRID)
    assert 300_000 < result["location_tons"] < 360_000
