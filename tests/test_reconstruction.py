"""Compare recovered cells with refactored APIs on an artificial fixture only."""
from itertools import product
from pathlib import Path
import ast

import nbformat
import numpy as np
import pandas as pd

from pension_risk import engines


def test_reconstructed_functions_agree_with_package(artificial_data):
    notebook = nbformat.read(Path(__file__).resolve().parents[1] /
                             "notebooks/appendix_reconstructed.ipynb", as_version=4)
    environment = {**artificial_data.arrays, "np": np, "pd": pd}
    code = [c.source for c in notebook.cells if c.cell_type == "code"]
    # Keep A.2's curve definitions; skip its file-loading statements on artificial input.
    functions = [node for node in ast.parse(code[1]).body if isinstance(node, ast.FunctionDef)]
    exec(compile(ast.Module(body=functions, type_ignores=[]), "A.2 curve definitions", "exec"), environment)
    for source in code[2:]:
        exec(compile(source, "appendix_reconstructed.ipynb", "exec"), environment)
    for name in ("run_baseline", "run_with_spreading", "run_with_reserve",
                 "run_with_hedge", "run_with_lifecycle", "run_with_longevity"):
        for actual, expected in zip(getattr(engines, name)(artificial_data), environment[name]()):
            np.testing.assert_allclose(actual, expected, rtol=1e-12)
    for projection in (0.025, 0.03, 0.04):
        np.testing.assert_allclose(engines.run_with_projection(artificial_data, projection)[1],
                                   environment["run_with_projection"](projection)[1], rtol=1e-12)
    for flags in product((False, True), repeat=4):
        np.testing.assert_allclose(engines.run(artificial_data, *flags)[1],
                                   environment["run"](*flags)[1], rtol=1e-12)
        for age in (25, 35, 45, 55, 67):
            np.testing.assert_allclose(engines.run_grid(artificial_data, age, *flags)[1],
                                       environment["run_grid"](age, *flags)[1], rtol=1e-12)
