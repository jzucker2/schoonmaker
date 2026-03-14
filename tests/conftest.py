"""Pytest fixtures for schoonmaker tests."""

from pathlib import Path

import pytest


# Repo root (parent of tests/)
REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_fdx_path() -> Path:
    """Path to the sample FDX fixture used by FDX parser tests."""
    return Path(__file__).parent / "fixtures" / "sample.fdx"


@pytest.fixture
def sample_fdx12_path() -> Path:
    """Path to FDX 12 sample (samples/); no DocumentRef."""
    return REPO_ROOT / "samples" / "final_draft_12_sample.fdx"


@pytest.fixture
def sample_fdx13_path() -> Path:
    """Path to FDX 13 sample (samples/); has DocumentRef."""
    return REPO_ROOT / "samples" / "final_draft_13_sample.fdx"
