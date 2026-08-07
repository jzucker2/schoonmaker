"""Tests for ``schoonmaker ci-label-pr``."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from schoonmaker.ci_label_pr import (
    DEFAULT_BRANCH_PREFIX,
    DEFAULT_LABEL,
    run_ci_label_pr,
    should_label_pr,
)


def _ok(
    stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr=stderr)


@pytest.mark.parametrize(
    "head_ref,prefix,expected",
    [
        ("writing/act-2", "writing/", True),
        ("writing/", "writing/", True),
        ("writing", "writing/", False),
        ("feature/x", "writing/", False),
        ("Writing/x", "writing/", False),
        ("", "writing/", False),
        ("writing/x", "", False),
        ("writing/x", "  ", False),
        ("  writing/x  ", "writing/", True),
    ],
)
def test_should_label_pr(head_ref, prefix, expected):
    assert should_label_pr(head_ref, prefix) is expected


def test_run_skips_when_prefix_mismatch(tmp_path, monkeypatch, capsys):
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))

    def fake_run(*a, **k):
        raise AssertionError("gh should not be called on skip")

    rc = run_ci_label_pr(
        pr_number=3,
        head_ref="feature/nope",
        token="tok",
        run=fake_run,
    )
    assert rc == 0
    assert "labeled=false" in out.read_text(encoding="utf-8")
    err = capsys.readouterr().err
    assert "does not start with" in err


def test_run_dry_run_would_label(tmp_path, monkeypatch, capsys):
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))

    def fake_run(*a, **k):
        raise AssertionError("gh should not be called on dry-run")

    rc = run_ci_label_pr(
        pr_number=9,
        head_ref="writing/scene-1",
        dry_run=True,
        token="tok",
        run=fake_run,
    )
    assert rc == 0
    assert "labeled=true" in out.read_text(encoding="utf-8")
    assert "dry-run" in capsys.readouterr().out


def test_run_adds_label_via_gh(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "schoonmaker.ci_label_pr.shutil.which",
        lambda name: "/usr/bin/gh" if name == "gh" else None,
    )
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    calls: list[list[str]] = []

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        calls.append(list(args))
        assert env is not None
        assert env.get("GH_TOKEN") == "tok"
        return _ok()

    rc = run_ci_label_pr(
        pr_number=12,
        head_ref="writing/act-2",
        label=DEFAULT_LABEL,
        branch_prefix=DEFAULT_BRANCH_PREFIX,
        token="tok",
        run=fake_run,
    )
    assert rc == 0
    assert calls == [
        ["gh", "pr", "edit", "12", "--add-label", "release-ready"]
    ]
    assert "labeled=true" in out.read_text(encoding="utf-8")


def test_run_fails_without_token(monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        "schoonmaker.ci_label_pr.shutil.which",
        lambda name: "/usr/bin/gh",
    )

    rc = run_ci_label_pr(
        pr_number=1,
        head_ref="writing/x",
        write_actions_output=False,
    )
    assert rc == 1


def test_run_resolves_env_refs(monkeypatch):
    monkeypatch.setenv("PR_NUMBER", "44")
    monkeypatch.setenv("PR_HEAD_REF", "writing/from-env")
    monkeypatch.setattr(
        "schoonmaker.ci_label_pr.shutil.which",
        lambda name: "/usr/bin/gh",
    )
    calls: list[list[str]] = []

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        calls.append(list(args))
        return _ok()

    rc = run_ci_label_pr(token="tok", run=fake_run, write_actions_output=False)
    assert rc == 0
    assert calls[0] == [
        "gh",
        "pr",
        "edit",
        "44",
        "--add-label",
        "release-ready",
    ]


def test_cli_ci_label_pr_dry_run_help():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-label-pr", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "branch-prefix" in r.stdout
    assert "release-ready" in r.stdout or "label" in r.stdout


def test_cli_ci_label_pr_dry_run_skip(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["GITHUB_OUTPUT"] = str(out)
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-label-pr",
            "--pr",
            "1",
            "--head-ref",
            "feature/x",
            "--dry-run",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "labeled=false" in out.read_text(encoding="utf-8")


def test_cli_ci_label_pr_dry_run_match(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    env = dict(os.environ)
    env["GITHUB_OUTPUT"] = str(out)
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "ci-label-pr",
            "--pr",
            "2",
            "--head-ref",
            "writing/ok",
            "--dry-run",
            "--label",
            "release-ready",
            "--branch-prefix",
            "writing/",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        env=env,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "dry-run" in r.stdout
    assert "labeled=true" in out.read_text(encoding="utf-8")
