"""Orchestrator: picks an initial energy mix from inputs, then runs all calcs.

This is the single entry point called from JavaScript via Pyodide.

Inputs dict keys (all strings unless noted):
  primary_goal, reliability, carbon_goal, geography, primary_workload,
  speed_to_power, cost_priority, rto, size_mw (int), type, ppa,
  grid_relationship, resilience, duration, pue (float)
"""

import json

from .lcoe import blended_lcoe, blended_components
from .capex import total_capex, capex_breakdown_by_tech
from .emissions import scope1, scope2
from .rto_signals import cfe_score
from .feasibility import feasibility_flag
from .recommendations import top_five
from .ira import lcoe_with_ira
from .resilience import apply_resilience, capex_premium
from .grid import apply_grid_relationship
from .sensitivity import tornado

# Mix presets keyed by primary goal. Values are fractions that sum to 1.0.
BASE_MIXES = {
    "Cost": {
        "natural_gas": 0.50, "wind": 0.25, "solar": 0.15, "bess": 0.05, "diesel": 0.05,
    },
    "Carbon": {
        "solar": 0.30, "wind": 0.25, "nuclear": 0.15, "geothermal": 0.10,
        "hydro": 0.10, "bess": 0.10,
    },
    "Reliability": {
        "nuclear": 0.30, "natural_gas": 0.25, "solar": 0.15, "wind": 0.10,
        "bess": 0.15, "diesel": 0.05,
    },
    "Balanced": {
        "solar": 0.22, "wind": 0.18, "natural_gas": 0.20, "nuclear": 0.15,
        "bess": 0.13, "hydro": 0.07, "geothermal": 0.05,
    },
}


# Pyodide mounts data at /data; tests can override via set_data_dir().
DATA_DIR = "/data"


def set_data_dir(path: str) -> None:
    """Point the loader at a different folder (used by pytest)."""
    global DATA_DIR
    DATA_DIR = path


def _load_json(name: str) -> dict:
    with open(f"{DATA_DIR}/{name}", "r") as f:
        return json.load(f)


def _adjust_for_carbon_goal(mix: dict, carbon_goal: str) -> dict:
    """If user wants 24/7 CFE, strip gas/diesel/coal and renormalize."""
    if carbon_goal == "24/7 Carbon-free":
        mix = {k: v for k, v in mix.items() if k not in {"natural_gas", "diesel", "coal"}}
    total = sum(mix.values())
    if total == 0:
        return mix
    return {k: round(v / total, 3) for k, v in mix.items()}


def _normalize(mix: dict) -> dict:
    total = sum(mix.values())
    if total == 0:
        return mix
    return {k: round(v / total, 3) for k, v in mix.items()}


def run_analysis(inputs: dict) -> dict:
    """Main entry point. Returns a JSON-serializable result dict."""
    atb        = _load_json("nrel_atb_2024.json")
    egrid      = _load_json("egrid_2022.json")
    eia        = _load_json("eia_capacity_factors.json")
    rto_hourly = _load_json("rto_hourly_sample.json")
    scope1_f   = _load_json("scope1_factors.json")
    iea_nze    = _load_json("iea_nze_benchmark.json")
    ira_data   = _load_json("ira_incentives.json")
    capex_comp = _load_json("capex_components.json")
    duck       = _load_json("duck_curve.json")

    # ── 1. Build the base mix from primary goal + adjustments ──
    mix = BASE_MIXES.get(inputs["primary_goal"], BASE_MIXES["Balanced"]).copy()
    mix = _adjust_for_carbon_goal(mix, inputs["carbon_goal"])
    mix = apply_grid_relationship(mix, inputs.get("grid_relationship", ""))
    mix = apply_resilience(mix, inputs.get("resilience", "Non-island"),
                           inputs.get("duration", "n/a"))
    mix = _normalize(mix)

    rto = inputs["rto"]
    size_mw = float(inputs["size_mw"])
    pue = float(inputs.get("pue", 1.4))
    # PUE inflates total demand: total_load = IT_load × PUE
    effective_mw = size_mw * pue

    premium = capex_premium(inputs.get("resilience", "Non-island"),
                            inputs.get("duration", "n/a"))

    # ── 2. Cost & emissions ──
    lcoe = blended_lcoe(mix, rto, atb, eia)
    lcoe_post_ira = lcoe_with_ira(lcoe, mix, rto, atb, eia, ira_data)
    capex = total_capex(mix, effective_mw, atb, premium=premium)

    s2 = scope2(mix, rto, effective_mw, egrid)
    s1 = scope1(mix, effective_mw, scope1_f)

    cfe = cfe_score(mix, rto, rto_hourly)
    feas = feasibility_flag(inputs)

    # ── 3. Chart-feeding extras ──
    lcoe_breakdown   = blended_components(mix, rto, atb, eia)
    capex_stack      = capex_breakdown_by_tech(mix, effective_mw, atb, capex_comp, premium=premium)
    sensitivity_rows = tornado(lcoe, capex, pue)
    iea_curve        = iea_nze.get("trajectory", {})
    duck_curve       = duck.get(rto, duck.get("_default", []))

    results = {
        "mix_pct": mix,
        "blended_lcoe_per_mwh": lcoe,
        "lcoe_post_ira": lcoe_post_ira,
        "lcoe_components": lcoe_breakdown,
        "total_capex_usd": capex,
        "capex_breakdown": capex_stack,
        "feasibility": feas,
        "emissions": {**s2, "scope1_tons": s1},
        "iea_nze": iea_curve,
        "duck_curve": duck_curve,
        "sensitivity": sensitivity_rows,
        "cfe_internal": cfe,  # kept for reliability/cost scatter, not surfaced as a card
        "pue": pue,
        "effective_mw": effective_mw,
        "rto": rto,
        "premium": premium,
        "tooltips": {
            "lcoe":        {
                "source": "NREL ATB 2024 — CapEx, O&M, fuel by tech & region.",
                "assumptions": "7% discount rate, 30-yr lifetime, ATB Moderate scenario.",
                "formula": "(CRF·CapEx + Fixed_OM)/(8760·CF/1000) + Var_OM + Fuel; mix-weighted.",
                "method":  "Per-tech LCOE then weighted by selected mix shares.",
            },
            "lcoe_post_ira": {
                "source": "IRS IRA §45/48 — ITC and PTC schedules.",
                "assumptions": "30% ITC for solar/storage/geothermal/hydro; $27.5/MWh wind PTC; $15/MWh nuclear PTC.",
                "formula": "ITC levelized via CRF; PTC subtracted directly $/MWh.",
                "method":  "Mix-weighted credit subtracted from blended LCOE.",
            },
            "capex": {
                "source": "NREL ATB 2024 capital cost ($/kW), per tech.",
                "assumptions": "Effective MW = IT × PUE; resilience premium applied.",
                "formula": "Σ (mix·effective_MW·1000·$/kW) × premium.",
                "method":  "Mix-weighted, scaled by PUE-adjusted size and island premium.",
            },
            "scope1": {
                "source": "EPA emission factors (CO2e lb/MWh) for fossil generation.",
                "assumptions": "Gas 819, diesel 1630, coal 2100 lb/MWh; renewables 0.",
                "formula": "Σ (mix·8760·effective_MW·factor) ÷ 2204.62.",
                "method":  "Direct on-site combustion only — no upstream methane.",
            },
            "scope2": {
                "source": "EPA eGRID 2022 — subregion grid emissions intensity.",
                "assumptions": "Location-based uses raw grid intensity; market-based credits carbon-free share.",
                "formula": "intensity·8760·effective_MW; market = (1 − cf_share)·location.",
                "method":  "GHG Protocol Scope 2 dual reporting.",
            },
            "feasibility": {
                "source": "LBNL Queued Up 2024 — interconnection queue waits by RTO.",
                "assumptions": "Queue wait vs user's speed-to-power bucket.",
                "formula": "Feasible if queue_years ≤ speed_to_power_years.",
                "method":  "Lookup table per RTO; reason string returned.",
            },
        },
    }
    results["recommendations"] = top_five(inputs, results)
    return results
