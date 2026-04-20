"""Fetch EPA eGRID 2022 emissions intensity by RTO.

eGRID publishes data at the subregion level (e.g. RFCE, SRTV). This script
maps subregions to RTOs using a hand-curated table, averages intensities
within each RTO, and writes a slim JSON.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd

EGRID_URL = "https://www.epa.gov/system/files/documents/2024-01/egrid2022_data.xlsx"

SUBREGION_TO_RTO = {
    "CAMX": "CAISO",
    "ERCT": "ERCOT",
    "SPSO": "SPP",  "SPNO": "SPP",
    "MROE": "MISO", "MROW": "MISO",
    "RFCE": "PJM",  "RFCW": "PJM",
    "NYUP": "NYISO","NYCW": "NYISO","NYLI": "NYISO",
    "NEWE": "ISO-NE",
}

OUT = Path(__file__).resolve().parents[1] / "data" / "egrid_2022.json"
META = OUT.parent / "_meta.json"


def main() -> None:
    print(f"Downloading {EGRID_URL} ...")
    df = pd.read_excel(EGRID_URL, sheet_name="SRL22", header=1)
    df = df[["SUBRGN", "SRCO2RTA"]].rename(
        columns={"SUBRGN": "subregion", "SRCO2RTA": "co2_lb_per_mwh"}
    )

    df["rto"] = df["subregion"].map(SUBREGION_TO_RTO)
    df = df.dropna(subset=["rto"])
    rto_avg = df.groupby("rto")["co2_lb_per_mwh"].mean().round(1).to_dict()

    out = {"_source": f"EPA eGRID 2022 fetched {date.today().isoformat()}",
           "_default": round(df["co2_lb_per_mwh"].mean(), 1)}
    out.update(rto_avg)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT}")

    meta = json.loads(META.read_text()) if META.exists() else {}
    meta["egrid_2022"] = {"refreshed": date.today().isoformat(), "source": "epa.gov/egrid"}
    META.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
