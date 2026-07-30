"""Tests for ``ci-select-pr`` and ``ci-release-notes``."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from schoonmaker.ci_release_notes import build_release_notes
from schoonmaker.ci_select_pr import SelectPrError, select_exactly_one_pr


def test_select_exactly_one_ok():
    pr = {"number": 7, "title": "Ship it"}
    assert select_exactly_one_pr([pr]) is pr


def test_select_exactly_one_none():
    with pytest.raises(SelectPrError, match="no open pull requests"):
        select_exactly_one_pr([], label="release-ready")


def test_select_exactly_one_many():
    with pytest.raises(SelectPrError, match="expected exactly one"):
        select_exactly_one_pr(
            [{"number": 1}, {"number": 2}],
            label="release-ready",
        )


def test_cli_ci_select_pr_success():
    repo_root = Path(__file__).resolve().parent.parent
    payload = json.dumps([{"number": 3, "title": "x", "url": "u"}])
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-select-pr",
            "--label",
            "release-ready",
        ],
        cwd=str(repo_root),
        input=payload,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert json.loads(r.stdout)["number"] == 3


def test_cli_ci_select_pr_none_exits_2():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-select-pr"],
        cwd=str(repo_root),
        input="[]",
        capture_output=True,
        text=True,
    )
    assert r.returncode == 2
    assert "no open pull requests" in r.stderr


def test_cli_ci_select_pr_many_exits_1():
    repo_root = Path(__file__).resolve().parent.parent
    payload = json.dumps([{"number": 1}, {"number": 2}])
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-select-pr"],
        cwd=str(repo_root),
        input=payload,
        capture_output=True,
        text=True,
    )
    assert r.returncode == 1
    assert "expected exactly one" in r.stderr


def test_cli_ci_select_pr_allow_empty_actions_output(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    out = tmp_path / "github_output"
    out.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["GITHUB_OUTPUT"] = str(out)
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-select-pr",
            "--allow-empty",
            "--actions-output",
        ],
        cwd=str(repo_root),
        input="[]",
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "skip=true" in out.read_text(encoding="utf-8")


def test_cli_ci_select_pr_actions_output_and_json(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    out = tmp_path / "github_output"
    out.write_text("", encoding="utf-8")
    json_out = tmp_path / "pr.json"
    payload = json.dumps(
        [
            {
                "number": 5,
                "title": "Ship",
                "url": "https://example.com/5",
                "baseRefOid": "abc",
            }
        ]
    )
    env = dict(os.environ)
    env["GITHUB_OUTPUT"] = str(out)
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-select-pr",
            "--actions-output",
            "--json-out",
            str(json_out),
        ],
        cwd=str(repo_root),
        input=payload,
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    text = out.read_text(encoding="utf-8")
    assert "skip=false" in text
    assert "pr_number=5" in text
    assert "base_sha=abc" in text
    assert json.loads(json_out.read_text(encoding="utf-8"))["number"] == 5


def test_append_github_output_multiline(tmp_path):
    from schoonmaker.ci_select_pr import append_github_output

    p = tmp_path / "out"
    append_github_output(p, {"a": "1", "b": "line1\nline2"})
    text = p.read_text(encoding="utf-8")
    assert "a=1\n" in text
    assert "b<<EOF\nline1\nline2\nEOF\n" in text


def test_build_release_notes_includes_report_and_pr(tmp_path):
    (tmp_path / "path-index.tsv").write_text("", encoding="utf-8")
    md = build_release_notes(
        tmp_path,
        version="v1.2.4",
        pr_number=9,
        pr_title="Nightly ship",
        pr_url="https://example.com/pull/9",
    )
    assert "## Release v1.2.4" in md
    assert "Merged [#9](https://example.com/pull/9): Nightly ship" in md
    assert "FDX diff report" in md


def test_cli_ci_release_notes(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    out = tmp_path / "notes.md"
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-release-notes",
            str(tmp_path),
            "--version",
            "v0.0.1",
            "--pr",
            "1",
            "-o",
            str(out),
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    text = out.read_text(encoding="utf-8")
    assert "## Release v0.0.1" in text
    assert "Merged #1" in text


def test_cli_helpers_help():
    repo_root = Path(__file__).resolve().parent.parent
    for cmd in ("ci-select-pr", "ci-release-notes"):
        r = subprocess.run(
            [sys.executable, "-m", "schoonmaker", cmd, "-h"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, (cmd, r.stdout, r.stderr)
