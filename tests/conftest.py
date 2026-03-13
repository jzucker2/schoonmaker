"""Pytest fixtures for schoonmaker tests."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_fdx_path() -> Path:
    """Path to the sample FDX fixture used by FDX parser tests."""
    return Path(__file__).parent / "fixtures" / "sample.fdx"
