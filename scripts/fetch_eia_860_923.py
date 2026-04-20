"""Aggregate EIA 860/923 capacity factors by technology and RTO.

EIA data is plant-level. We join generators (860) with generation (923),
classify each plant's RTO by state, compute annual capacity factor, and
average by (tech, rto).

This is the most complex fetch script. The shape of the final JSON is
small and simple; the work is mainly reshaping.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

STATE_TO_RTO = {
    "TX": "ERCOT",
    "CA": "CAISO",
    "NY": "NYISO",
    "ME": "ISO-NE", "NH": "ISO-NE", "VT": "ISO-NE", "MA": "ISO-NE",
    "RI": "ISO-NE", "CT": "ISO-NE",
    "PA": "PJM", "NJ": "PJM", "DE": "PJM", "MD": "PJM", "VA": "PJM",
    "WV": "PJM", "OH": "PJM", "KY": "PJM", "DC": "PJM",
    "IL": "MISO", "IN": "MISO", "MI": "MISO", "WI": "MISO",
    "MN": "MISO", "IA": "MISO", "MO": "MISO", "AR": "MISO", "LA": "MISO",
    "KS": "SPP", "OK": "SPP", "NE": "SPP", "ND": "SPP", "SD": "SPP",
}

FUEL_TO_TECH = {
    "SUN": "solar",
    "WND": "wind",
    "GEO": "geothermal",
    "NG":  "natural_gas",
    "COL": "coal",
    "DFO": "diesel",
    "MWH": "bess",
}

OUT = Path(__file__).resolve().parents[1] / "site" / "data" / "eia_capacity_factors.json"
META = OUT.parent / "_meta.json"

GENS_URL = "https://www.eia.gov/electricity/data/eia860/archive/xls/eia8602023.zip"
GEN_URL  = "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2023.zip"


def main() -> None:
    # Placeholder: real implementation downloads both ZIPs, reads the relevant
    # sheets, joins on plant_id, and computes CF = annual_MWh / (nameplate_MW * 8760).
    # Kept as a scaffold so the user can fill in the download+parse when ready.
    print("Not yet implemented — seed file already committed. "
          "Implement download + join logic here as a Python exercise.")
    print(f"Target output: {OUT}")

    meta = json.loads(META.read_text()) if META.exists() else {}
    meta["eia_capacity_factors"] = {"refreshed": date.today().isoformat(),
                                    "source": "eia.gov", "note": "seed only"}
    META.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
