"""Command-line entry point for reproducible SARRA-Py runs."""

import argparse

from .application import execute_config
from ._version import __version__


def main(argv=None):
    parser = argparse.ArgumentParser(prog="sarra-py", description="Run SARRA-Py from a YAML configuration")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("config", help="YAML configuration file")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing output NetCDF")
    args = parser.parse_args(argv)
    try:
        output = execute_config(args.config, overwrite=args.overwrite)
    except (OSError, TypeError, ValueError, KeyError) as exc:
        parser.exit(2, f"sarra-py: {exc}\n")
    print(output)
    return 0
