from pathlib import Path
from runpy import run_path

from setuptools import find_packages, setup


ROOT = Path(__file__).resolve().parent


def parse_requirements(filename):
    return [
        requirement
        for line in (ROOT / filename).read_text(encoding="utf-8").splitlines()
        if (requirement := line.partition("#")[0].strip())
    ]


setup(
    name="SARRA-Py",
    version=run_path(str(ROOT / "src" / "sarra_py" / "_version.py"))["__version__"],
    python_requires=">=3.8",
    description="Daily spatial crop simulation from the SARRA model family",
    long_description=(ROOT / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="Jérémy LAVARENNE (@codename5281)",
    url="https://github.com/SARRA-cropmodels/SARRA-Py",
    license_files=("LICENCE",),
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=parse_requirements("requirements.txt"),
    extras_require={
        "notebooks": parse_requirements("requirements-notebooks.txt"),
        "dev": ["build", "pytest", "twine", "wheel"],
    },
    entry_points={"console_scripts": ["sarra-py=sarra_py.cli:main"]},
)
