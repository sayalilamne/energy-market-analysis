"""Rule-based top-5 strategic recommendations.

Rules are (condition_fn, message_template) pairs. We evaluate them in order,
keep the first 5 that match, and return their formatted messages.

Keep rules short and specific so they stay meaningful.
"""


def _r(cond, msg):
    return (cond, msg)


# Each condition takes (inputs, results) dicts and returns bool.
RULES = [
    _r(
        lambda i, r: i["rto"] == "ERCOT" and i["primary_workload"] == "AI-Training",
        "ERCOT + AI-Training: pair solar with BESS to align with daytime training peaks.",
    ),
    _r(
        lambda i, r: i["carbon_goal"] == "24/7 Carbon-free",
        "24/7 CFE goal: supplement VPPAs with on-site geothermal or firm renewables.",
    ),
    _r(
        lambda i, r: i["speed_to_power"] == "<2 years" and i["rto"] != "ERCOT",
        "Sub-2-year timeline outside ERCOT: explore behind-the-meter gas bridge with CCUS optionality.",
    ),
    _r(
        lambda i, r: i["size_mw"] >= 500 and i["type"] == "Hyperscale",
        "Hyperscale (>=500 MW): negotiate tier-1 PPAs and co-locate with transmission upgrades.",
    ),
    _r(
        lambda i, r: i["reliability"] == "Five Nines (99.999%)",
        "Five Nines reliability: add N+2 diesel/gas backup and a minimum 4-hour BESS buffer.",
    ),
    _r(
        lambda i, r: i["primary_goal"] == "Cost",
        "Cost-first: weight mix toward wind + gas CCGT where ATB LCOE is lowest.",
    ),
    _r(
        lambda i, r: i["primary_goal"] == "Carbon",
        "Carbon-first: prioritize solar + wind + geothermal; backfill with BESS over gas.",
    ),
    _r(
        lambda i, r: i["geography"] == "Pacific Northwest",
        "Pacific Northwest: leverage hydro-backed grid intensity for low market-based Scope 2.",
    ),
    _r(
        lambda i, r: i["ppa"] == "none",
        "No PPA: all mix must be on-site or behind-the-meter; budget for higher CapEx.",
    ),
    _r(
        lambda i, r: r["feasibility"]["flag"] == "Not Feasible",
        "Feasibility flag: revisit RTO selection or stretch speed-to-power to 5+ years.",
    ),
]


def top_five(inputs: dict, results: dict) -> list:
    """Return up to 5 recommendation strings matched against current inputs/results."""
    out = []
    for cond, msg in RULES:
        try:
            if cond(inputs, results):
                out.append(msg)
        except KeyError:
            continue
        if len(out) == 5:
            break
    # Ensure we always return 5 items, padding with a generic if needed.
    while len(out) < 5:
        out.append("Consider revisiting inputs to refine the recommendation set.")
    return out
