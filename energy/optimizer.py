"""Orchestrator: picks an initial energy mix from inputs, then runs all calcs.

This is the single entry point called from JavaScript via Pyodide.

Inputs dict keys (all strings unless noted):
  primary_goal, reliability, carbon_goal, geography, primary_workload,
  speed_to_power, cost_priority, rto, size_mw (int), type, ppa
"""

import json

from .lcoe import blended_lcoe
from .capex import total_capex
from .emissions import scope2
from .rto_signals import cfe_score
from .feasibility import feasibility_flag
from .recommendations import top_five

# Mix presets keyed by primary goal. Values are fractions that sum to 1.0.
# These are intentionally simple; real optimization can replace this later.
BASE_MIXES = {
    "Cost": {
        "natural_gas": 0.50, "wind": 0.25, "solar": 0.15, "bess": 0.05, "diesel": 0.05,
    },
    "Carbon": {
        "solar": 0.40, "wind": 0.35, "geothermal": 0.15, "bess": 0.10,
    },
    "Reliability": {
        "natural_gas": 0.40, "solar": 0.20, "wind": 0.15, "bess": 0.15, "diesel": 0.10,
    },
    "Balanced": {
        "solar": 0.30, "wind": 0.25, "natural_gas": 0.25, "bess": 0.15, "geothermal": 0.05,
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
    """If user wants 24/7 CFE, strip gas/diesel and renormalize."""
    if carbon_goal == "24/7 Carbon-free":
        mix = {k: v for k, v in mix.items() if k not in {"natural_gas", "diesel", "coal"}}
    total = sum(mix.values())
    if total == 0:
        return mix
    return {k: round(v / total, 3) for k, v in mix.items()}


def run_analysis(inputs: dict) -> dict:
    """Main entry point. Returns a JSON-serializable result dict."""
    atb = _load_json("nrel_atb_2024.json")
    egrid = _load_json("egrid_2022.json")
    eia = _load_json("eia_capacity_factors.json")
    rto_hourly = _load_json("rto_hourly_sample.json")

    mix = BASE_MIXES.get(inputs["primary_goal"], BASE_MIXES["Balanced"]).copy()
    mix = _adjust_for_carbon_goal(mix, inputs["carbon_goal"])

    rto = inputs["rto"]
    size_mw = float(inputs["size_mw"])

    lcoe = blended_lcoe(mix, rto, atb, eia)
    capex = total_capex(mix, size_mw, atb)
    emissions = scope2(mix, rto, size_mw, egrid)
    cfe = cfe_score(mix, rto, rto_hourly)
    feas = feasibility_flag(inputs)

    results = {
        "mix_pct": mix,
        "blended_lcoe_per_mwh": lcoe,
        "total_capex_usd": capex,
        "carbon_free_score": cfe,
        "feasibility": feas,
        "emissions": emissions,
        "tooltips": {
            "lcoe": "NREL ATB 2024 CapEx, O&M, fuel. Formula: (CRF*CapEx+Fixed_OM)/(8760*CF)+VarOM+Fuel, weighted.",
            "capex": "Sum of mix_share * size_MW * 1000 * $/kW from NREL ATB 2024.",
            "emissions": "EPA eGRID 2022 intensity (lb/MWh) * 8760 hrs * size_MW, converted to metric tons.",
            "cfe": "Weighted: 30% grid avg CFE share (gridstatus) + 70% on-site renewable share.",
            "feasibility": "LBNL Queued Up typical queue wait vs user's Speed-to-Power bucket.",
        },
    }
    results["recommendations"] = top_five(inputs, results)
    return results
