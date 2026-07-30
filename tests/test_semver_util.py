"""Tests for semver helpers and ``next-semver`` CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from schoonmaker.semver_util import (
    bump_patch,
    format_semver,
    latest_semver_tag,
    next_patch_from_tags,
    parse_semver,
)


def test_parse_semver_with_and_without_v():
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert parse_semver("v1.2.3") == (1, 2, 3)
    assert parse_semver("v0.0.9") == (0, 0, 9)


def test_parse_semver_rejects_garbage():
    with pytest.raises(ValueError, match="not a semver"):
        parse_semver("not-a-version")
    with pytest.raises(ValueError, match="not a semver"):
        parse_semver("1.2")


def test_bump_patch_preserves_v_prefix():
    assert bump_patch("1.2.3") == "1.2.4"
    assert bump_patch("v1.2.3") == "v1.2.4"
    assert bump_patch("v0.0.0") == "v0.0.1"


def test_format_semver():
    assert format_semver(1, 0, 0) == "v1.0.0"
    assert format_semver(1, 0, 0, prefix_v=False) == "1.0.0"


def test_latest_semver_tag_picks_highest():
    tags = ["v0.9.9", "v1.0.0", "not-semver", "v1.0.1", "2.0.0"]
    assert latest_semver_tag(tags) == "2.0.0"


def test_latest_semver_tag_empty():
    assert latest_semver_tag([]) is None


def test_next_patch_from_tags_default_when_empty():
    assert next_patch_from_tags([]) == "v0.0.1"
    assert next_patch_from_tags([], default="v1.0.0") == "v1.0.1"


def test_next_patch_from_tags_bumps_latest():
    assert next_patch_from_tags(["v1.2.3", "v1.2.2"]) == "v1.2.4"


def test_cli_next_semver_bump_positional():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "next-semver", "v1.3.1"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert r.stdout.strip() == "v1.3.2"


def test_cli_next_semver_from_tags(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@e.co"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "T"],
        cwd=repo,
        check=True,
    )
    (repo / "f").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "add", "f"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "c"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "tag", "v0.1.0"], cwd=repo, check=True)
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "next-semver",
            "--from-tags",
            "--repo",
            str(repo),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert r.stdout.strip() == "v0.1.1"


def test_cli_next_semver_help():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "next-semver", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "from-tags" in r.stdout
