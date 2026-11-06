"""A.2: numeric workbook loading with source-bound NPZ caching."""

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from .acquisition import KNOWN_SHA256, RELEASE, sha256_file

SHEETS = {
    "equity": "4_Aandelenrendement",
    "infl_nl": "6_Prijsinflatie_NL",
    "s1": "1_Toestandsvariabele_1",
    "s2": "2_Toestandsvariabele_2",
    "s3": "3_Toestandsvariabele_3",
    "phi_N": "7_Renteparameter_phi_N",
    "Psi_N": "8_Renteparameter_Psi_N",
    "phi_R_NL": "11_Renteparameter_phi_R_NL",
    "Psi_R": "10_Renteparameter_Psi_R",
}
CACHE_SCHEMA = 1


@dataclass
class ScenarioData:
    arrays: dict[str, np.ndarray]
    provenance: dict = field(default_factory=dict)

    @property
    def n_scen(self):
        return self.arrays["equity"].shape[0]

    def require_horizon(self, return_years):
        """Returns are intervals t..t+1; states/phi include time zero."""
        for key in ("equity", "infl_nl"):
            if self.arrays[key].shape[1] < return_years:
                raise ValueError(f"{key} does not cover {return_years} return years")
        for key in ("s1", "s2", "s3", "phi_N", "phi_R_NL"):
            if self.arrays[key].shape[1] < return_years + 1:
                raise ValueError(f"{key} needs time 0 through {return_years}")


def validate_arrays(arrays, expected_scenarios=20000, expected_years=100):
    """Validate the inspected workbook layout; never infer/remove a time column."""
    expected = {
        "equity": (expected_scenarios, expected_years),
        "infl_nl": (expected_scenarios, expected_years),
        **{k: (expected_scenarios, expected_years + 1) for k in ("s1", "s2", "s3")},
        "phi_N": (100, expected_years + 1),
        "phi_R_NL": (100, expected_years + 1),
        "Psi_N": (100, 3), "Psi_R": (100, 3),
    }
    for key, shape in expected.items():
        arr = arrays[key]
        if arr.shape != shape or not np.isfinite(arr).all():
            raise ValueError(f"{key}: expected finite numeric array {shape}; found {arr.shape}")


def read_sheet(book, name):
    arr = pd.read_excel(book, sheet_name=name, header=None).to_numpy(dtype=float)
    arr = arr[~np.all(np.isnan(arr), axis=1)]
    return arr[:, ~np.all(np.isnan(arr), axis=0)]


def load_workbook(path, cache_dir="data/cache"):
    """Load only the exact downloaded unshocked 20K 2026Q2 P-set.

    Any local filename/path is accepted. Bytes must match the recorded release.
    Caches are keyed by the full workbook SHA-256 and loader schema, and their
    embedded metadata and numeric layouts are checked on every load.
    """
    path = Path(path)
    fingerprint = sha256_file(path)
    if fingerprint != KNOWN_SHA256:
        raise ValueError("Workbook SHA-256 differs from the acquired 2026Q2 P-set. "
                         "Check the official source and data/provenance.json; no substitution is made.")
    metadata = {"dataset": RELEASE, "sha256": fingerprint, "cache_schema": CACHE_SCHEMA}
    cache_dir = Path(cache_dir)
    cache = cache_dir / f"cp2022-p-2026q2-v{CACHE_SCHEMA}-{fingerprint}.npz"
    if cache.exists():
        with np.load(cache, allow_pickle=False) as z:
            if json.loads(str(z["metadata"])) != metadata:
                raise ValueError(f"Cache metadata mismatch: {cache.name}")
            arrays = {key: z[key] for key in SHEETS}
    else:
        with pd.ExcelFile(path, engine="calamine") as book:
            missing = set(SHEETS.values()) - set(book.sheet_names)
            if missing:
                raise ValueError(f"Missing required sheets: {sorted(missing)}")
            arrays = {key: read_sheet(book, name) for key, name in SHEETS.items()}
        validate_arrays(arrays)
        cache_dir.mkdir(parents=True, exist_ok=True)
        temporary = cache.with_suffix(".tmp.npz")
        np.savez_compressed(temporary, **arrays, metadata=json.dumps(metadata, sort_keys=True))
        temporary.replace(cache)
    validate_arrays(arrays)
    data = ScenarioData(arrays, metadata)
    data.require_horizon(69)
    return data
