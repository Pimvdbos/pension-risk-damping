"""A.13 output numbering is separate from Section 6 Tables 1-4."""

import pandas as pd

from .config import FULL, GRID, MECHS


def result_tables(study, ages=GRID):
    """Retain all seven appendix tables, including sequential addition."""
    baseline = pd.DataFrame([
        {"Age": age, **{k: study.get(age)[k] for k in ("Mean", "Std", "CoV", "P5", "P95")}}
        for age in ages
    ]).round(4)
    base45 = study.get(45)["CoV"]
    names = {"spreading": "Spreading", "reserve": "Reserve",
             "hedge": "Protection return", "lifecycle": "Lifecycle"}
    standalone = pd.DataFrame([
        {"Mechanism": names[m], "Mean": (p := study.get(45, {m}))["Mean"],
         "CoV": p["CoV"], "Delta CoV": base45 - p["CoV"], "Tail P95": p["P95"]}
        for m in MECHS
    ]).sort_values("Delta CoV", ascending=False).round(4)
    steps = [("None", set()), ("Spreading", {"spreading"}),
             ("+Reserve", {"spreading", "reserve"}),
             ("+Hedge", {"spreading", "reserve", "hedge"}), ("+Lifecycle", set(FULL))]
    sequential = pd.DataFrame([
        {"Step": name, "CoV": (p := study.get(45, active))["CoV"],
         "Reduction": base45 - p["CoV"], "% Reduction": 100 * (base45 - p["CoV"]) / base45}
        for name, active in steps
    ]).round(3)
    comparison = pd.DataFrame([
        {"Age": age, "Baseline CoV": (b := study.get(age)["CoV"]),
         "Full CoV": (f := study.get(age, FULL)["CoV"]),
         "Abs reduction": b - f, "% reduction": 100 * (1 - f / b)} for age in ages
    ]).round(3)
    level = study.shapley_table("CoV", ages)
    yoy = study.shapley_table("YoY", ages)
    shares = ["Age"] + [f"{m}_share" for m in MECHS]
    columns = ["Age", "Spreading %", "Reserve %", "Protection Return %", "Lifecycle %"]
    level_shares, yoy_shares = level[shares].copy(), yoy[shares].copy()
    level_shares.columns = yoy_shares.columns = columns
    return {"appendix_table1_baseline": baseline,
            "appendix_table2_standalone_age45": standalone,
            "appendix_table3_sequential_age45": sequential,
            "appendix_table4_cohort_comparison": comparison,
            "appendix_table5_shapley_values": level.round(4),
            "appendix_table6_shapley_level_shares": level_shares.round(1),
            "appendix_table7_shapley_yoy_shares": yoy_shares.round(1)}
