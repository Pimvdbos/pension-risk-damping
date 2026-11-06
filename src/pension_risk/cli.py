"""Small demonstrations by default; full research execution requires --full."""

import argparse
import hashlib
import json
import platform
from importlib.metadata import version
from time import perf_counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from .acquisition import FILENAME, download
from .config import GRID, MECHS, Settings
from .data import load_workbook
from .engines import run_with_longevity, run_with_projection
from .metrics import describe
from .shapley import CoalitionStudy, coalitions
from .tables import result_tables


def implementation_hash():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob("*.py")):
        digest.update(path.name.encode())
        digest.update(path.read_text(encoding="utf-8").encode("utf-8"))
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("download", help="Explicit optional 179 MB DNB download")
    analyze = commands.add_parser("analyze", help="Generate appendix result tables")
    analyze.add_argument("--workbook", type=Path, default=Path("data/raw") / FILENAME)
    analyze.add_argument("--cache-dir", type=Path, default=Path("data/cache"))
    selection = analyze.add_mutually_exclusive_group()
    selection.add_argument("--scenarios", type=int, default=256, help="First N scenarios, demonstration only")
    selection.add_argument("--full", action="store_true", help="Explicit full 20,000-scenario research workflow")
    analyze.add_argument("--extensions", action="store_true", help="Also run separate A.8/A.9 illustrations")
    analyze.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    if args.command == "download":
        print(json.dumps(download(), indent=2))
        return
    started = perf_counter()
    started_at = datetime.now(timezone.utc).isoformat()
    data = load_workbook(args.workbook, args.cache_dir)
    count = data.n_scen if args.full else args.scenarios
    if not 2 <= count <= data.n_scen:
        parser.error(f"--scenarios must be between 2 and {data.n_scen}")
    if not args.full and count == data.n_scen:
        parser.error("Use --full to execute all 20,000 scenarios")
    label = "full_research_run" if args.full else f"demonstration_first_{count}"
    output = args.output or Path("results/generated") / label
    if "reported" in output.parts:
        parser.error("Generated output must not be written under results/reported")
    settings = Settings()
    provenance = {
        "execution": label,
        "purpose": "Scenario calculation; agreement with the report is assessed separately",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "data": data.provenance, "parameters": asdict(settings),
        "cohort_ages": GRID, "scenario_selection": {"first": 0, "count": count},
        "implementation_sha256": implementation_hash(), "extensions": args.extensions,
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        **{name: version(name) for name in ("numpy", "pandas", "python-calamine")}},
    }
    # Reuse only summaries with identical source, implementation and parameters.
    identity = {k: v for k, v in provenance.items() if k != "created_at_utc"}
    output.mkdir(parents=True, exist_ok=True)
    cache_path = output / "coalition_summaries.json"
    study = CoalitionStudy(data, settings, np.arange(count))
    if cache_path.exists():
        saved = json.loads(cache_path.read_text(encoding="utf-8"))
        if saved["identity"] == json.loads(json.dumps(identity)):
            study.summaries = {(r["age"], frozenset(r["active"])): r["metrics"] for r in saved["rows"]}
    for age in GRID:
        for active in coalitions():
            study.get(age, active)
        print(f"Completed age {age}: all 16 coalitions ({label})", flush=True)
    for name, table in result_tables(study).items():
        table.to_csv(output / f"{name}.csv", index=False)
    if args.extensions:
        rows = [{"extension": f"projection_{p:.3f}",
                 **describe(run_with_projection(data, p, scenarios=np.arange(count))[1])}
                for p in (0.025, 0.03, 0.04)]
        rows.append({"extension": "illustrative_longevity",
                     **describe(run_with_longevity(data, scenarios=np.arange(count))[1])})
        pd.DataFrame(rows).to_csv(output / "illustrative_extensions.csv", index=False)
    rows = [{"age": age, "active": sorted(active), "metrics": metrics}
            for (age, active), metrics in study.summaries.items()]
    cache_path.write_text(json.dumps({"identity": identity, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    provenance.update(started_at_utc=started_at,
                      completed_at_utc=datetime.now(timezone.utc).isoformat(),
                      wall_time_seconds=perf_counter() - started)
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {label} to {output}. See original report for published estimates.")


if __name__ == "__main__":
    main()
