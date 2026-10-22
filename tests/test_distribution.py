import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import zipfile


def test_source_archive_builds_an_importable_wheel(tmp_path):
    root = Path(__file__).resolve().parents[1]
    source = tmp_path / "source"
    source.mkdir()
    for name in (
        "setup.py", "pyproject.toml", "requirements.txt",
        "requirements-notebooks.txt", "MANIFEST.in", "README.md", "CHANGELOG.md", "LICENCE",
    ):
        shutil.copy2(root / name, source / name)
    for name in ("src", "docs", "tests"):
        shutil.copytree(
            root / name, source / name,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    shutil.copytree(root / "data" / "params", source / "data" / "params")

    def command(arguments, cwd, env=None):
        process = subprocess.run(
            [sys.executable, *arguments], cwd=cwd, env=env,
            text=True, capture_output=True,
        )
        assert process.returncode == 0, process.stdout + process.stderr
        return process.stdout

    command(["setup.py", "sdist", "--dist-dir", str(tmp_path / "dist")], source)
    archive = next((tmp_path / "dist").glob("*.tar.gz"))
    unpacked = tmp_path / "unpacked"
    with tarfile.open(archive) as bundle:
        names = bundle.getnames()
        assert not any("/docs/dev/" in name for name in names)
        assert not any("/benchmarks/" in name for name in names)
        assert not any(name.endswith("/test_benchmark_smoke.py") for name in names)
        assert any(name.endswith("/requirements.txt") for name in names)
        assert any(name.endswith("/requirements-notebooks.txt") for name in names)
        # This archive is produced above from the controlled local source tree.
        if sys.version_info >= (3, 12):
            bundle.extractall(unpacked, filter="data")
        else:
            bundle.extractall(unpacked)
    extracted = next(unpacked.iterdir())
    environment = dict(os.environ, PIP_NO_INDEX="1", PIP_DISABLE_PIP_VERSION_CHECK="1")
    command([
        "-m", "pip", "wheel", str(extracted), "--no-deps", "--no-build-isolation",
        "--wheel-dir", str(tmp_path / "wheels"),
    ], tmp_path, environment)

    wheel = next((tmp_path / "wheels").glob("*.whl"))
    installed = tmp_path / "installed"
    with zipfile.ZipFile(wheel) as bundle:
        metadata = bundle.read(
            next(name for name in bundle.namelist() if name.endswith(".dist-info/METADATA"))
        ).decode()
        assert "Version: 0.2.0\n" in metadata
        assert "Provides-Extra: notebooks" in metadata
        assert "Requires-Dist: geopandas" in metadata
        assert "Requires-Dist: dask" in metadata
        bundle.extractall(installed)
    environment["PYTHONPATH"] = str(installed)
    output = command(
        ["-c", "import sarra_py; assert sarra_py.__version__ == '0.2.0'; print(sarra_py.__file__)"], tmp_path, environment,
    )
    assert str(installed) in output
    assert "usage: sarra-py" in command(["-m", "sarra_py", "--help"], tmp_path, environment)

    assert command(["-m", "sarra_py", "--version"], tmp_path, environment).strip() == "sarra-py 0.2.0"
