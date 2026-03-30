"""Tests for ``ci-fdx-diff`` / ``schoonmaker.ci_fdx_diff``."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

from schoonmaker.ci_fdx_diff import (
    list_changed_fdx_paths,
    main_ci_fdx_diff,
    path_fingerprint,
    resolve_base_sha,
    run_ci_fdx_diff,
)


def test_path_fingerprint_matches_sha256_of_utf8_path():
    p = "folder/script.fdx"
    assert path_fingerprint(p) == hashlib.sha256(p.encode("utf-8")).hexdigest()


def test_resolve_base_sha_prefers_explicit_base():
    assert resolve_base_sha("aaa", "bbb") == "aaa"


def test_resolve_base_sha_requires_head():
    assert resolve_base_sha("aaa", "") is None
    assert resolve_base_sha("aaa", "   ") is None


def test_resolve_base_sha_null_base_uses_parent(monkeypatch):
    calls: list[list[str]] = []

    def fake_git(args, *, cwd=None, check=False):
        calls.append(list(args))
        assert args[:2] == ["rev-parse", "--verify"]
        assert args[2] == "dead^"
        return subprocess.CompletedProcess(
            args, 0, stdout="parent-sha\n", stderr=""
        )

    monkeypatch.setattr("schoonmaker.ci_fdx_diff._git", fake_git)
    out = resolve_base_sha("0" * 40, "dead")
    assert out == "parent-sha"


def test_resolve_base_sha_no_parent_returns_none(monkeypatch):
    def fake_git(args, *, cwd=None, check=False):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="")

    monkeypatch.setattr("schoonmaker.ci_fdx_diff._git", fake_git)
    assert resolve_base_sha("", "abc123") is None


def test_list_changed_fdx_paths_normalizes_backslashes(monkeypatch):
    def fake_git(args, *, cwd=None, check=False):
        return subprocess.CompletedProcess(
            args,
            0,
            stdout="a\\b\\file.fdx\n",
            stderr="",
        )

    monkeypatch.setattr("schoonmaker.ci_fdx_diff._git", fake_git)
    assert list_changed_fdx_paths("b", "h") == ["a/b/file.fdx"]


def test_list_changed_fdx_paths_git_failure_raises(monkeypatch):
    def fake_git(args, *, cwd=None, check=False):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="bad")

    monkeypatch.setattr("schoonmaker.ci_fdx_diff._git", fake_git)
    with pytest.raises(RuntimeError, match="git diff failed"):
        list_changed_fdx_paths("b", "h")


def test_main_ci_fdx_diff_passes_repo(tmp_path, monkeypatch):
    captured: dict = {}

    def fake_run(out, base, head, *, repo=None):
        captured["repo"] = repo
        return 0

    monkeypatch.setattr("schoonmaker.ci_fdx_diff.run_ci_fdx_diff", fake_run)
    args = SimpleNamespace(
        output=str(tmp_path / "out"),
        base_sha="a",
        head_sha="b",
        repo=str(tmp_path),
    )
    assert main_ci_fdx_diff(args) == 0
    assert captured["repo"] == tmp_path.resolve()


def test_run_ci_fdx_diff_skips_when_no_base(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(
        "schoonmaker.ci_fdx_diff.resolve_base_sha",
        lambda *a, **k: None,
    )
    rc = run_ci_fdx_diff(tmp_path / "out", "", "head")
    assert rc == 0
    err = capsys.readouterr().err
    assert "no base commit" in err


@pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")
def test_run_ci_fdx_diff_git_integration(sample_fdx_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy(sample_fdx_path, repo / "script.fdx")
    try:
        subprocess.run(
            ["git", "init"],
            cwd=repo,
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or b"") + (e.stdout or b"")
        pytest.skip(f"git init unavailable: {err!r}")
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
    subprocess.run(["git", "add", "script.fdx"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "first"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    r = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    base_sha = r.stdout.strip()
    text = (repo / "script.fdx").read_text(encoding="utf-8")
    (repo / "script.fdx").write_text(
        text.replace("Hello?", "Hello!", 1),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "script.fdx"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "second"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    r2 = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    head_sha = r2.stdout.strip()
    out = tmp_path / "reports"
    rc = run_ci_fdx_diff(out, base_sha, head_sha, repo=repo)
    assert rc == 0
    safe = path_fingerprint("script.fdx")
    assert (out / f"{safe}-diff.json").is_file()
    assert "_tmp" not in [p.name for p in out.iterdir()]


def test_cli_ci_fdx_diff_help():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-fdx-diff", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "output" in r.stdout.lower() or "--output" in r.stdout
