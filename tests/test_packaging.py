"""Check executable notebook syntax and links without a workbook in CI."""
import ast
from pathlib import Path
import re

import nbformat
import numpy as np
import pytest

from pension_risk.data import validate_arrays, load_workbook

ROOT = Path(__file__).resolve().parents[1]


def test_notebook_validity_sections_and_syntax():
    notebook = nbformat.read(ROOT / "notebooks/appendix_reconstructed.ipynb", as_version=4)
    nbformat.validate(notebook)
    assert len([c for c in notebook.cells if c.cell_type == "code"]) == 13
    for cell in notebook.cells:
        if cell.cell_type == "code":
            ast.parse(cell.source)
            assert cell.outputs == [] and cell.execution_count is None
    for section in range(1, 14):
        assert any(c.source.startswith(f"## A.{section} ") for c in notebook.cells)


def test_markdown_local_links_and_images_exist():
    for doc in ROOT.rglob("*.md"):
        if any(part.startswith(".") or part == "tmp" for part in doc.relative_to(ROOT).parts):
            continue
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("#"):
                continue
            assert (doc.parent / target.split("#")[0]).exists(), (doc, target)


def test_wrong_workbook_cannot_reuse_cache(tmp_path):
    source = tmp_path / "other.xlsx"
    source.write_bytes(b"artificial wrong source")
    with pytest.raises(ValueError, match="SHA-256 differs"):
        load_workbook(source, tmp_path)


def test_scenario_time_alignment_rejected():
    arrays = {"equity": np.zeros((2, 3)), "infl_nl": np.zeros((2, 2))}
    with pytest.raises(ValueError, match="infl_nl"):
        validate_arrays(arrays, expected_scenarios=2, expected_years=3)
