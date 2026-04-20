"""Fetch NREL ATB 2024 cost/performance baseline data.

Run locally:
    python scripts/fetch_nrel_atb.py

Writes site/data/nrel_atb_2024.json. Commit the result.

What this script does (reading top to bottom):
  1. Download the ATB CSV from NREL.
  2. Keep only the technologies this tool uses.
  3. Reshape into a flat dict: tech -> {capex_per_kw, fixed_om, ...}.
  4. Save as JSON.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

ATB_URL = "https://atb-archive.nrel.gov/electricity/2024/data/ATBe.csv"

TECH_MAP = {
    "UtilityPV":     "solar",
    "LandbasedWind": "wind",
    "Geothermal":    "geothermal",
    "NaturalGas":    "natural_gas",
    "Coal":          "coal",
    "Biopower":      "diesel",
    "Battery":       "bess",
}

OUT = Path(__file__).resolve().parents[1] / "site" / "data" / "nrel_atb_2024.json"
META = OUT.parent / "_meta.json"


def main() -> None:
    print(f"Downloading {ATB_URL} ...")
    df = pd.read_csv(ATB_URL)

    df = df[(df["core_metric_case"] == "Market") & (df["core_metric_variable"] == 2024)]

    result = {}
    for atb_name, tech_key in TECH_MAP.items():
        rows = df[df["technology"] == atb_name]
        if rows.empty:
            continue
        result[tech_key] = {
            "capex_per_kw": float(rows[rows["core_metric_parameter"] == "CAPEX"]["value"].mean()),
            "fixed_om":     float(rows[rows["core_metric_parameter"] == "Fixed O&M"]["value"].mean()),
            "variable_om":  float(rows[rows["core_metric_parameter"] == "Variable O&M"]["value"].mean()),
            "fuel_cost":    float(rows[rows["core_metric_parameter"] == "Fuel"]["value"].mean() or 0),
            "lifetime":     30,
        }

    result["_source"] = f"NREL ATB 2024 fetched {date.today().isoformat()}"
    OUT.write_text(json.dumps(result, indent=2))
    print(f"Wrote {OUT}")

    meta = json.loads(META.read_text()) if META.exists() else {}
    meta["nrel_atb_2024"] = {"refreshed": date.today().isoformat(), "source": "atb.nrel.gov"}
    META.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
