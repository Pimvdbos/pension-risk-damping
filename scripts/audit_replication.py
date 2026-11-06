"""Full-data audit, recovered-notebook execution and compact reproducibility snapshot.

Run the ordinary --full --extensions workflow first. Requires the dev dependencies.
No input parameters are changed to obtain agreement with the report.
"""

import argparse
import contextlib
import hashlib
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import nbformat
import numpy as np
import pandas as pd

from pension_risk.acquisition import FILENAME, sha256_file
from pension_risk.cli import implementation_hash
from pension_risk.config import GRID, MECHS
from pension_risk.curves import nominal_curve, real_curve_nl
from pension_risk.data import load_workbook
from pension_risk.engines import run_grid
from pension_risk import engines
from pension_risk.metrics import describe
from pension_risk.replication import compare_reported, factorial_diagnostics
from pension_risk.shapley import CoalitionStudy, coalitions, shapley_values

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = (1000, 2000, 5000, 10000, 20000)


def curve_reference_checks(data, workbook):
    reference = pd.read_excel(workbook, sheet_name="VoorbeeldRTS", engine="calamine", header=None)
    reference = reference.iloc[2:102]
    rows = []
    for t, offset in ((0, 0), (1, 5)):
        maturities = reference.iloc[:, offset].to_numpy(dtype=int)
        for name, function, column in (("nominal", nominal_curve, offset + 1),
                                        ("real_nl", real_curve_nl, offset + 3)):
            expected = reference.iloc[:, column].to_numpy(dtype=float)
            actual = function(data, t, maturities, [0])[0]
            difference = actual - expected
            rows.append({"curve": name, "time": t, "scenario_zero_based": 0,
                         "maturities_checked": len(maturities),
                         "max_absolute_error": float(np.max(np.abs(difference))),
                         "root_mean_squared_error": float(np.sqrt(np.mean(difference ** 2))),
                         "passes_absolute_tolerance_1e-12": bool(np.all(np.abs(difference) <= 1e-12))})
    return pd.DataFrame(rows)


def execute_notebook():
    notebook_path = ROOT / "notebooks/appendix_reconstructed.ipynb"
    notebook = nbformat.read(notebook_path, as_version=4)
    nbformat.validate(notebook)
    previous = os.environ.get("PENSION_SCENARIOS")
    os.environ["PENSION_SCENARIOS"] = "all"
    environment = {"__name__": "__main__"}
    log_path = ROOT / "results/generated/audit_notebook.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    try:
        with log_path.open("w", encoding="utf-8") as log, contextlib.redirect_stdout(log):
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    exec(compile(cell.source, "appendix_reconstructed.ipynb", "exec"), environment)
                    count += 1
    finally:
        if previous is None:
            os.environ.pop("PENSION_SCENARIOS", None)
        else:
            os.environ["PENSION_SCENARIOS"] = previous
    return environment, count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=ROOT / "data/raw" / FILENAME)
    parser.add_argument("--run-dir", type=Path, default=ROOT / "results/generated/full_research_run")
    parser.add_argument("--output", type=Path, default=ROOT / "results/generated/full_research_audit")
    args = parser.parse_args()
    if Path.cwd().resolve() != ROOT:
        parser.error("Run this script from the repository root")
    if args.output.resolve().is_relative_to(ROOT / "results/reported"):
        parser.error("The supplied report tables must remain unchanged")
    started = perf_counter()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    provenance = json.loads((args.run_dir / "provenance.json").read_text(encoding="utf-8"))
    if provenance["scenario_selection"] != {"first": 0, "count": 20000} or not provenance["extensions"]:
        parser.error("First execute pension-risk analyze --full --extensions")
    if provenance["implementation_sha256"] != implementation_hash():
        parser.error("Source changed since the run; rerun the full workflow")
    data = load_workbook(args.workbook, ROOT / "data/cache")
    if provenance["data"] != data.provenance:
        parser.error("Full-run source data provenance mismatch")
    saved = json.loads((args.run_dir / "coalition_summaries.json").read_text(encoding="utf-8"))
    study = CoalitionStudy(data)
    study.summaries = {(r["age"], frozenset(r["active"])): r["metrics"] for r in saved["rows"]}
    expected = {(age, s) for age in GRID for s in coalitions()}
    if set(study.summaries) != expected:
        parser.error("The run must contain exactly all 80 age/coalition summaries")
    print("Comparing all four report tables and both Shapley implementations", flush=True)
    comparison = compare_reported(study, ROOT / "results/reported")
    marginal, shapley_checks, interactions = factorial_diagnostics(study)
    reference = curve_reference_checks(data, args.workbook)
    print("Executing all 13 recovered notebook cells on 20,000 scenarios", flush=True)
    os.environ["PENSION_WORKBOOK"] = str(args.workbook.resolve())
    notebook, cell_count = execute_notebook()
    print("Checking all 80 recovered-cohort summaries; computing prefix diagnostics", flush=True)
    parity, paths, prefixes, quantiles = [], [], [], []
    for age in GRID:
        for active in coalitions():
            nominal, real = notebook["run_grid"](age, **{m: m in active for m in MECHS})
            summary = describe(real)
            for metric, value in summary.items():
                expected_value = study.get(age, active)[metric]
                parity.append({"age": age, "coalition": "+".join(sorted(active)) or "baseline", "metric": metric,
                               "absolute_error": abs(value - expected_value),
                               "agrees": bool(np.isclose(value, expected_value, rtol=1e-11, atol=1e-12))})
            paths.append({"age": age, "coalition": "+".join(sorted(active)) or "baseline",
                          "finite": bool(np.isfinite(nominal).all() and np.isfinite(real).all()),
                          "positive": bool(np.all(nominal > 0) and np.all(real > 0)),
                          "min_nominal": float(np.min(nominal)), "min_real": float(np.min(real)),
                          "max_real": float(np.max(real))})
            if age == 45:
                for n in PREFIXES:
                    prefixes.append({"scenarios": n, "active": active, "metrics": describe(real[:n])})
                if active in (frozenset(), frozenset(MECHS)):
                    p5, median, p95 = np.percentile(real, [5, 50, 95], axis=0)
                    for year in range(real.shape[1]):
                        quantiles.append({"configuration": "Full model" if active else "Baseline",
                                          "payment_number": year + 1, "p5": p5[year],
                                          "median": median[year], "p95": p95[year],
                                          "mean": np.mean(real[:, year])})
        print(f"Checked all coalitions at age {age}", flush=True)
    parity, paths = pd.DataFrame(parity), pd.DataFrame(paths)
    standalone_checks = []
    for name, argument_sets in [("run_baseline", [()]), ("run_with_spreading", [()]),
                                ("run_with_reserve", [()]), ("run_with_hedge", [()]),
                                ("run_with_lifecycle", [()]), ("run_with_longevity", [()]),
                                ("run_with_projection", [(0.025,), (0.03,), (0.04,)])]:
        for arguments in argument_sets:
            recovered = notebook[name](*arguments)
            maintained = getattr(engines, name)(data, *arguments)
            for kind, actual, expected_array in zip(("nominal", "real"), maintained, recovered):
                standalone_checks.append({"function": name, "arguments": str(arguments), "benefit_type": kind,
                                          "max_absolute_array_error": float(np.max(np.abs(actual - expected_array))),
                                          "agrees": bool(np.allclose(actual, expected_array, rtol=1e-11, atol=1e-12))})
    standalone_checks = pd.DataFrame(standalone_checks)
    notebook_shapley = []
    for metric, name in (("CoV", "shapley_df"), ("YoY", "shapley_df_yoy")):
        recovered = notebook[name].set_index("Age")
        for age in GRID:
            phi, total = study.shapley_for_age(age, metric)
            for mechanism, value in phi.items():
                notebook_shapley.append({"age": age, "metric": metric, "mechanism": mechanism,
                                         "absolute_error": abs(value - recovered.loc[age, f"{mechanism}_value"])})
    prefix_lookup = {(r["scenarios"], r["active"]): r["metrics"] for r in prefixes}
    stability = []
    for n in PREFIXES:
        for metric in ("CoV", "YoY"):
            base = prefix_lookup[n, frozenset()][metric]
            full = prefix_lookup[n, frozenset(MECHS)][metric]
            values = {s: base - prefix_lookup[n, s][metric] for s in coalitions()}
            phi = shapley_values(values)
            total = base - full
            stability.append({"scenarios": n, "metric": metric, "baseline_risk": base,
                              "full_risk": full, "reduction_percent": 100 * total / base,
                              **{f"{m}_share_percent": 100 * phi[m] / total for m in MECHS}})
    summaries = pd.DataFrame([{"age": a, "coalition": "+".join(sorted(s)) or "baseline", **metrics}
                              for (a, s), metrics in study.summaries.items()])
    tables = {"reported_comparison": comparison, "coalition_metrics": summaries,
              "marginal_contributions": marginal, "shapley_checks": shapley_checks,
              "pair_interactions_age45": interactions, "curve_reference_checks": reference,
              "notebook_package_comparison": parity, "path_checks": paths,
              "standalone_array_checks": standalone_checks,
              "notebook_shapley_comparison": pd.DataFrame(notebook_shapley),
              "scenario_prefix_stability": pd.DataFrame(stability),
              "benefit_quantiles_age45": pd.DataFrame(quantiles)}
    tables["cohort_baseline_full"] = pd.DataFrame([
        {"age": age, "baseline_mean": (b := study.get(age))["Mean"],
         "full_mean": (f := study.get(age, MECHS))["Mean"],
         "baseline_level_cov": b["CoV"], "full_level_cov": f["CoV"],
         "level_reduction_percent": 100 * (1 - f["CoV"] / b["CoV"]),
         "baseline_yoy": b["YoY"], "full_yoy": f["YoY"],
         "yoy_reduction_percent": 100 * (1 - f["YoY"] / b["YoY"])} for age in GRID
    ])
    for name, frame in tables.items():
        frame.to_csv(output / f"{name}.csv", index=False, float_format="%.15g", lineterminator="\n")
    for path in args.run_dir.glob("*.csv"):
        (output / path.name).write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    (output / "run_provenance.json").write_text((args.run_dir / "provenance.json").read_text(encoding="utf-8"),
                                                encoding="utf-8", newline="\n")
    verdict = {"reported_cells_compared": len(comparison),
               "reported_cells_matching_rounding": int(comparison.matches_published_rounding.sum()),
               "notebook_code_cells_executed": cell_count, "notebook_scenarios": data.n_scen,
               "notebook_package_comparisons": len(parity), "all_notebook_metrics_agree": bool(parity.agrees.all()),
               "standalone_array_comparisons": len(standalone_checks),
               "all_standalone_arrays_agree": bool(standalone_checks.agrees.all()),
               "max_notebook_shapley_error": float(pd.DataFrame(notebook_shapley).absolute_error.max()),
               "all_paths_finite_and_positive": bool(paths.finite.all() and paths.positive.all()),
               "curve_values_checked": int(reference.maturities_checked.sum()),
               "all_curve_checks_pass": bool(reference["passes_absolute_tolerance_1e-12"].all()),
               "max_shapley_efficiency_residual": float(shapley_checks.efficiency_residual.abs().max()),
               "max_shapley_permutation_difference": float(shapley_checks.max_permutation_difference.abs().max()),
               "negative_marginal_level_reductions": int(marginal[(marginal.metric == "CoV")].risk_increases.sum()),
               "negative_marginal_yoy_reductions": int(marginal[(marginal.metric == "YoY")].risk_increases.sum())}
    (output / "audit_summary.json").write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8", newline="\n")
    files = sorted(p for p in output.iterdir() if p.suffix in (".csv", ".json") and p.name != "audit_provenance.json")
    source_files = sorted((ROOT / "src/pension_risk").glob("*.py")) + [Path(__file__), ROOT / "scripts/plot_replicated_results.py", ROOT / "notebooks/appendix_reconstructed.ipynb"]
    manifest = {"completed_at_utc": datetime.now(timezone.utc).isoformat(),
                "wall_time_seconds": perf_counter() - started,
                "source_identity": "Content hashes identify the audited source; no parent Git revision is asserted",
                "report_edition": "34-page portfolio edition with original research pagination",
                "implementation_sha256": implementation_hash(), "data": data.provenance,
                "report_sha256": sha256_file(ROOT / "reports/Management_Control_Assignment.pdf"),
                "source_hash_normalization": "UTF-8 text with CRLF/CR normalized to LF; data/report/output hashes remain raw bytes",
                "source_files_sha256": {p.relative_to(ROOT).as_posix():
                                        hashlib.sha256(p.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                                        for p in source_files},
                "reported_table_sha256": {p.name: sha256_file(p) for p in (ROOT / "results/reported").glob("*.csv")},
                "output_sha256": {p.name: sha256_file(p) for p in files},
                "environment": {"python": platform.python_version(), "platform": platform.platform(),
                                **{name: version(name) for name in ("numpy", "pandas", "python-calamine", "nbformat")}},
                "scope": "Numerical replication of the fixed recovered model; not validation of real-world policy assumptions",
                "prefix_diagnostics": "Nested first-N subsets, not independent samples or confidence intervals"}
    (output / "audit_provenance.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(verdict, indent=2))
    if not (comparison.matches_published_rounding.all() and parity.agrees.all() and standalone_checks.agrees.all()
            and pd.DataFrame(notebook_shapley).absolute_error.max() < 1e-12 and paths.finite.all()
            and paths.positive.all() and reference["passes_absolute_tolerance_1e-12"].all()
            and shapley_checks.efficiency_residual.abs().max() < 1e-12
            and shapley_checks.max_permutation_difference.max() < 1e-12):
        raise SystemExit("Audit discrepancies recorded; inspect the diagnostic CSVs")


if __name__ == "__main__":
    main()
