"""Pull one representative week of hourly RTO generation via gridstatus.

gridstatus wraps each RTO's public data feed in a single Python API.
For v1 we only need the *average carbon-free share* per RTO (used to score
24/7 CFE matching). The script also keeps the raw hourly frame so a future
version can score true hour-by-hour matching.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import gridstatus
import pandas as pd

CFE_FUELS = {"solar", "wind", "hydro", "nuclear", "geothermal"}

RTOS = {
    "CAISO":  gridstatus.CAISO,
    "ERCOT":  gridstatus.Ercot,
    "SPP":    gridstatus.SPP,
    "MISO":   gridstatus.MISO,
    "PJM":    gridstatus.PJM,
    "NYISO":  gridstatus.NYISO,
    "ISO-NE": gridstatus.ISONE,
}

OUT = Path(__file__).resolve().parents[1] / "site" / "data" / "rto_hourly_sample.json"
META = OUT.parent / "_meta.json"


def cf_share_for(iso) -> float:
    """Return average carbon-free share across the last 7 full days."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=7)
    df = iso().get_fuel_mix(start=start, end=end)

    # gridstatus returns wide-format: cols = fuel names, rows = timestamps.
    df.columns = [c.lower() for c in df.columns]
    cfe_cols = [c for c in df.columns if c in CFE_FUELS]
    other_cols = [c for c in df.columns if c not in cfe_cols and c != "time"]

    cfe_total = df[cfe_cols].sum(axis=1)
    grand_total = df[cfe_cols + other_cols].sum(axis=1).replace(0, pd.NA)
    return float((cfe_total / grand_total).mean())


def main() -> None:
    out = {"_source": f"gridstatus 7-day avg fetched {date.today().isoformat()}"}
    for name, iso in RTOS.items():
        try:
            out[name] = {"avg_cf_share": round(cf_share_for(iso), 3)}
            print(f"{name}: {out[name]}")
        except Exception as exc:
            print(f"{name}: skipped ({exc})")
            out[name] = {"avg_cf_share": 0.30, "note": "fetch failed, default"}

    OUT.write_text(json.dumps(out, indent=2))
    print(f"Wrote {OUT}")

    meta = json.loads(META.read_text()) if META.exists() else {}
    meta["rto_hourly_sample"] = {"refreshed": date.today().isoformat(), "source": "gridstatus"}
    META.write_text(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
