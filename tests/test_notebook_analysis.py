"""Check the actual example analysis cells without external climate/survey data."""
import ast
import json
from pathlib import Path
import subprocess

import numpy as np
import pytest

NOTEBOOKS = Path(__file__).resolve().parents[1] / "notebooks"
pytestmark = pytest.mark.skipif(not NOTEBOOKS.is_dir(), reason="Notebooks are supplied in the Git checkout")


def cells(pattern):
    path = next(NOTEBOOKS.glob(pattern))
    return json.loads(path.read_text(encoding="utf-8"))["cells"]


def test_tracked_notebook_code_has_valid_syntax():
    root = NOTEBOOKS.parent
    paths = subprocess.check_output(["git", "-c", f"safe.directory={root}",
                                     "ls-files", "notebooks/*.ipynb"], cwd=root, text=True).splitlines()
    assert paths
    for relative in paths:
        for index, cell in enumerate(json.loads((root / relative).read_text(encoding="utf-8"))["cells"]):
            if cell["cell_type"] != "code":
                continue
            source = "\n".join("pass" if line.lstrip().startswith(("%", "!")) else line
                               for line in "".join(cell["source"]).splitlines())
            ast.parse(source, filename=f"{relative}:cell{index}")


@pytest.mark.parametrize("example", [10, 11])
def test_notebook_trend_diagnostic_has_required_import_and_detects_linear_series(example):
    cell = next(c for c in cells(f"*Exemple {example}*.ipynb")
                if "def mann_kendall_with_sen_slope" in "".join(c["source"]))
    namespace = {"np": np}
    exec("".join(cell["source"]), namespace)
    slope, p_value, trend = namespace["mann_kendall_with_sen_slope"](np.arange(10.))
    assert slope == pytest.approx(1.)
    assert p_value < .05
    assert trend == 1.
