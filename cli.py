#!/usr/bin/env python3
"""Thin wrapper so ``python cli.py`` still works; prefer ``schoonmaker`` or ``python -m schoonmaker``."""  # noqa: E501

from __future__ import annotations

from schoonmaker.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
