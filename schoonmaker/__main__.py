"""Allow ``python -m schoonmaker`` (same as the ``schoonmaker`` console script)."""  # noqa: E501

from __future__ import annotations

from schoonmaker.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
