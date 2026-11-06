"""Artificial audit fixtures and structural model properties; no report targets."""
import numpy as np
import pytest
import hashlib
import json
from pathlib import Path
import pandas as pd

from pension_risk.config import MECHS
from pension_risk.engines import run_grid
from pension_risk.replication import rounding_comparison, shapley_from_permutations, compare_reported
from pension_risk.shapley import coalitions, shapley_values, CoalitionStudy


def test_comparison_uses_display_precision_without_refitting():
    assert rounding_comparison(1.23, 1.234, 2)["matches_published_rounding"]
    assert not rounding_comparison(1.23, 1.236, 2)["matches_published_rounding"]
    row = rounding_comparison(1.23, 1.234, 2)
    assert row["rounding_half_unit"] == pytest.approx(0.005)
    assert row["signed_error"] == pytest.approx(0.004)


def test_permutation_formula_with_complementarity_and_substitution():
    def value(s):
        return len(s) + (2 if {"hedge", "lifecycle"} <= s else 0) - (0.5 if {"spreading", "reserve"} <= s else 0)
    values = {s: value(s) for s in coalitions()}
    assert shapley_values(values) == pytest.approx(shapley_from_permutations(values))
    assert sum(shapley_from_permutations(values).values()) == pytest.approx(values[frozenset(MECHS)])


@pytest.mark.parametrize("spreading,reserve", [(False, False), (True, False), (False, True), (True, True)])
def test_full_payout_hedge_removes_lifecycle_effect_on_relative_paths(artificial_data, spreading, reserve):
    # At retirement h=1, so lifecycle affects accumulated capital, not payout returns.
    # Spreading and reserve rules are homogeneous in starting benefits.
    base = run_grid(artificial_data, 45, hedge=True, spreading=spreading, reserve=reserve)[1]
    life = run_grid(artificial_data, 45, hedge=True, lifecycle=True, spreading=spreading, reserve=reserve)[1]
    np.testing.assert_allclose(base / base[:, [0]], life / life[:, [0]], atol=1e-12, rtol=1e-12)


def test_committed_replication_snapshot_integrity():
    root = Path(__file__).resolve().parents[1]
    snapshot = root / "results/replication/2026q2"
    manifest = json.loads((snapshot / "audit_provenance.json").read_text(encoding="utf-8"))
    for name, expected in manifest["output_sha256"].items():
        assert hashlib.sha256((snapshot / name).read_bytes()).hexdigest() == expected, name
    for name, expected in manifest["source_files_sha256"].items():
        normalized = (root / name).read_text(encoding="utf-8").encode("utf-8")
        assert hashlib.sha256(normalized).hexdigest() == expected, name
    for name, expected in manifest["reported_table_sha256"].items():
        assert hashlib.sha256((root / "results/reported" / name).read_bytes()).hexdigest() == expected, name


def test_published_snapshot_recompares_to_supplied_tables_without_workbook():
    root = Path(__file__).resolve().parents[1]
    metrics = pd.read_csv(root / "results/replication/2026q2/coalition_metrics.csv")
    study = CoalitionStudy(None)
    for _, row in metrics.iterrows():
        active = frozenset() if row.coalition == "baseline" else frozenset(row.coalition.split("+"))
        study.summaries[int(row.age), active] = {key: row[key] for key in ("Mean", "Std", "CoV", "YoY", "P5", "P95")}
    comparison = compare_reported(study, root / "results/reported")
    assert comparison.matches_published_rounding.all()
