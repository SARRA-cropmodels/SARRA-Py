"""Allow ``python -m sarra_py`` to use the same CLI as ``sarra-py``."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
