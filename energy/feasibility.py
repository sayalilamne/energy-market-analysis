"""Feasibility flag based on LBNL 'Queued Up' interconnection queue data.

Typical queue wait times (years) per RTO, summarized from LBNL 2023 report.
If the user's desired speed-to-power is shorter than the queue, flag as
'Not Feasible' with a reason.
"""

TYPICAL_QUEUE_YEARS = {
    "CAISO": 4.5,
    "ERCOT": 2.0,
    "SPP": 4.0,
    "MISO": 4.5,
    "PJM": 5.0,
    "NYISO": 3.5,
    "ISO-NE": 3.0,
}

SPEED_BUCKET_MAX_YEARS = {
    "<2 years": 2,
    "2-5 years": 5,
    "5+ years": 10,
}


def feasibility_flag(inputs: dict) -> dict:
    """Return {'flag': 'Feasible'|'Not Feasible', 'reason': str}."""
    rto = inputs.get("rto", "PJM")
    speed = inputs.get("speed_to_power", "2-5 years")
    max_years = SPEED_BUCKET_MAX_YEARS.get(speed, 5)
    queue = TYPICAL_QUEUE_YEARS.get(rto, 4.0)

    if queue <= max_years:
        return {
            "flag": "Feasible",
            "reason": f"{rto} typical queue ~{queue} yrs fits within '{speed}'.",
        }
    return {
        "flag": "Not Feasible",
        "reason": (
            f"{rto} typical queue ~{queue} yrs exceeds '{speed}'. "
            "Consider ERCOT, behind-the-meter generation, or longer timeline."
        ),
    }
