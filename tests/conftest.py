"""Source-tree test configuration."""
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

# Local performance experiments are kept outside the maintained test suite.
collect_ignore = ["test_benchmark_smoke.py"]
