"""Report-precision comparison and factorial diagnostics; no model recalibration."""

from itertools import permutations
from pathlib import Path

import pandas as pd

from .config import GRID, MECHS
from .shapley import coalitions, shapley_values

NAMES = {"Baseline (no damping)": frozenset(), "Baseline": frozenset(),
         "Protection return": frozenset({"hedge"}), "Lifecycle": frozenset({"lifecycle"}),
         "Spreading": frozenset({"spreading"}), "Reserve": frozenset({"reserve"})}


def rounding_comparison(reported, reproduced, decimal_places):
    """Compare at the published decimal precision, not a fitted relative tolerance."""
    return {"reported": float(reported), "reproduced": float(reproduced),
            "decimal_places": decimal_places, "rounding_half_unit": 0.5 * 10 ** -decimal_places,
            "signed_error": float(reproduced - reported),
            "matches_published_rounding": format(reproduced, f".{decimal_places}f") ==
                                          format(reported, f".{decimal_places}f")}


def shapley_from_permutations(values, players=MECHS):
    """Independent 24-ordering calculation to check the coalition-weight formula."""
    orders = list(permutations(players))
    contributions = dict.fromkeys(players, 0.0)
    for order in orders:
        previous = frozenset()
        for player in order:
            following = previous | {player}
            contributions[player] += (values[following] - values[previous]) / len(orders)
            previous = following
    return contributions


def compare_reported(study, reported_dir):
    """All 93 numerical outcome cells from Section 6 Tables 1-4."""
    reported_dir = Path(reported_dir)
    rows = []

    def record(table, key, metric, value, actual, places):
        rows.append({"report_table": table, "key": key, "metric": metric,
                     **rounding_comparison(float(value), float(actual), places)})

    one = pd.read_csv(reported_dir / "table1_standalone_age45.csv")
    mapping = {"mean_real_benefit": ("Mean", 4), "std_real_benefit": ("Std", 4),
               "level_cov": ("CoV", 4), "delta_level_cov": (None, 4),
               "yoy_volatility": ("YoY", 3)}
    for _, row in one.iterrows():
        p = study.get(45, NAMES[row.configuration])
        for column, (metric, places) in mapping.items():
            if pd.notna(row[column]):
                actual = p[metric] if metric else study.get(45)["CoV"] - p["CoV"]
                record(1, row.configuration, column, row[column], actual, places)
    two = pd.read_csv(reported_dir / "table2_shapley_shares.csv")
    for _, row in two.iterrows():
        mechanism = next(iter(NAMES[row.mechanism]))
        for age in GRID:
            phi, total = study.shapley_for_age(age, "CoV")
            record(2, f"age={age};{row.mechanism}", "level_share_percent",
                   row[f"level_age{age}_percent"], 100 * phi[mechanism] / total, 1)
        phi, total = study.shapley_for_age(45, "YoY")
        record(2, f"age=45;{row.mechanism}", "yoy_share_percent", row.yoy_age45_percent,
               100 * phi[mechanism] / total, 1)
    three = pd.read_csv(reported_dir / "table3_standalone_cohorts.csv")
    for _, row in three.iterrows():
        for age in GRID:
            record(3, f"age={age};{row.configuration}", "level_cov", row[f"level_age{age}"],
                   study.get(age, NAMES[row.configuration])["CoV"], 3)
    four = pd.read_csv(reported_dir / "table4_baseline_full.csv")
    for _, row in four.iterrows():
        age = int(row.current_age)
        baseline, full = study.get(age)["CoV"], study.get(age, MECHS)["CoV"]
        for metric, actual, places in [("baseline_level_cov", baseline, 3),
                                       ("full_level_cov", full, 3),
                                       ("absolute_reduction", baseline - full, 3),
                                       ("reduction_percent", 100 * (1 - full / baseline), 1)]:
            record(4, f"age={age}", metric, row[metric], actual, places)
    return pd.DataFrame(rows)


def factorial_diagnostics(study):
    """Marginal contributions, pair-only interactions and exact attribution checks."""
    marginal, checks, interactions = [], [], []
    for age in GRID:
        for metric in ("CoV", "YoY"):
            base = study.get(age)[metric]
            values = {s: base - study.get(age, s)[metric] for s in coalitions()}
            phi = shapley_values(values)
            alternate = shapley_from_permutations(values)
            checks.append({"age": age, "metric": metric,
                           "full_reduction": values[frozenset(MECHS)],
                           "efficiency_residual": sum(phi.values()) - values[frozenset(MECHS)],
                           "max_permutation_difference": max(abs(phi[m] - alternate[m]) for m in MECHS)})
            for s in coalitions():
                for mechanism in MECHS:
                    if mechanism not in s:
                        delta = values[s | {mechanism}] - values[s]
                        marginal.append({"age": age, "metric": metric, "coalition": "+".join(sorted(s)) or "baseline",
                                         "added": mechanism, "marginal_reduction": delta,
                                         "risk_increases": delta < -1e-12})
            if age == 45:
                for i, first in enumerate(MECHS):
                    for second in MECHS[i + 1:]:
                        interactions.append({"age": age, "metric": metric, "first": first, "second": second,
                                             "pair_reduction": values[frozenset({first, second})],
                                             "sum_standalone_reductions": values[frozenset({first})] + values[frozenset({second})],
                                             "pair_only_interaction": values[frozenset({first, second})] -
                                                                      values[frozenset({first})] - values[frozenset({second})]})
    return pd.DataFrame(marginal), pd.DataFrame(checks), pd.DataFrame(interactions)
