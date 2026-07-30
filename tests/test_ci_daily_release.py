"""Tests for ``schoonmaker ci-daily-release`` orchestration."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from schoonmaker.ci_daily_release import (
    DEFAULT_LABEL,
    run_ci_daily_release,
)


def _ok(
    stdout: str = "", stderr: str = ""
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], 0, stdout=stdout, stderr=stderr)


def test_run_ci_daily_release_skips_when_no_prs(tmp_path, monkeypatch):
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh" if name == "gh" else None,
    )

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        assert args[:3] == ["gh", "pr", "list"]
        return _ok(stdout="[]")

    rc = run_ci_daily_release(
        repo=tmp_path,
        token="tok",
        run=fake_run,
        append_step_summary=False,
    )
    assert rc == 0
    assert "skip=true" in out.read_text(encoding="utf-8")


def test_run_ci_daily_release_fails_when_many_prs(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh",
    )

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        return _ok(stdout=json.dumps([{"number": 1}, {"number": 2}]))

    rc = run_ci_daily_release(
        repo=tmp_path,
        token="tok",
        run=fake_run,
        write_actions_output=False,
        append_step_summary=False,
    )
    assert rc == 1


def test_run_ci_daily_release_happy_path(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh",
    )
    out = tmp_path / "ghub_out"
    out.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    calls: list[list[str]] = []
    rev_parse_n = {"n": 0}
    fdx_kwargs: dict = {}

    pr = {
        "number": 12,
        "title": "Ship script",
        "url": "https://example.com/12",
        "baseRefOid": "stalebase",
        "headRefOid": "headhead",
    }

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        calls.append(list(args))
        if args[:3] == ["gh", "pr", "list"]:
            return _ok(stdout=json.dumps([pr]))
        if args[:3] == ["gh", "pr", "merge"]:
            assert "--squash" in args
            # Pre-merge tip must be recorded before merge.
            assert any(
                c[:2] == ["git", "rev-parse"] and "origin/" in c[-1]
                for c in calls[:-1]
            )
            return _ok()
        if args[:2] == ["git", "fetch"]:
            return _ok()
        if args[:2] == ["git", "checkout"]:
            return _ok()
        if args[:2] == ["git", "reset"]:
            return _ok()
        if args[:2] == ["git", "rev-parse"]:
            rev_parse_n["n"] += 1
            if rev_parse_n["n"] == 1:
                assert args[-1].startswith("origin/")
                return _ok(stdout="aaaabbbb\n")
            return _ok(stdout="deadbeef\n")
        if args[:3] == ["gh", "release", "create"]:
            return _ok()
        if args[:3] == ["gh", "pr", "comment"]:
            return _ok()
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.next_patch_from_tags",
        lambda repo=None: "v0.0.1",
    )

    def fake_fdx(*a, **k):
        fdx_kwargs.update(k)
        assert a[1] == "aaaabbbb"
        assert a[2] == "deadbeef"
        return 0

    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.run_ci_fdx_diff",
        fake_fdx,
    )
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.build_release_notes",
        lambda *a, **k: "## Release v0.0.1\n\n",
    )

    rc = run_ci_daily_release(
        repo=tmp_path,
        token="tok",
        run=fake_run,
        append_step_summary=False,
    )
    assert rc == 0
    text = out.read_text(encoding="utf-8")
    assert "skip=false" in text
    assert "pr_number=12" in text
    assert "tag=v0.0.1" in text
    assert "base_sha=aaaabbbb" in text
    assert "head_sha=deadbeef" in text
    assert fdx_kwargs.get("list_items") is False
    assert fdx_kwargs.get("display_boards") is False
    notes = tmp_path / "RELEASE_NOTES.md"
    assert notes.is_file()
    assert any(c[:3] == ["gh", "release", "create"] for c in calls)
    assert any(c[:3] == ["gh", "pr", "comment"] for c in calls)


def test_run_ci_daily_release_step_summary_once(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh",
    )
    summary = tmp_path / "summary.md"
    summary.write_text("", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    rev_parse_n = {"n": 0}
    pr = {
        "number": 1,
        "title": "t",
        "url": "https://example.com/1",
    }

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        if args[:3] == ["gh", "pr", "list"]:
            return _ok(stdout=json.dumps([pr]))
        if args[:2] == ["git", "rev-parse"]:
            rev_parse_n["n"] += 1
            sha = "basebase\n" if rev_parse_n["n"] == 1 else "headhead\n"
            return _ok(stdout=sha)
        return _ok()

    notes_body = "## Release v0.0.1\n\nMerged #1\n\n## FDX diff report\n\nok\n"
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.next_patch_from_tags",
        lambda repo=None: "v0.0.1",
    )
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.run_ci_fdx_diff",
        lambda *a, **k: 0,
    )
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.build_release_notes",
        lambda *a, **k: notes_body,
    )

    rc = run_ci_daily_release(
        repo=tmp_path,
        token="tok",
        run=fake_run,
        write_actions_output=False,
    )
    assert rc == 0
    text = summary.read_text(encoding="utf-8")
    assert text.count("## FDX diff report") == 1
    assert text.count("## Release v0.0.1") == 1


def test_run_ci_daily_release_honors_board_env(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh",
    )
    monkeypatch.setenv("CI_FDX_LIST_ITEMS", "1")
    monkeypatch.setenv("CI_FDX_DISPLAY_BOARDS", "true")
    rev_parse_n = {"n": 0}
    captured: dict = {}

    def fake_run(args, *, cwd=None, check=True, env=None, input_text=None):
        if args[:3] == ["gh", "pr", "list"]:
            return _ok(stdout=json.dumps([{"number": 2, "title": "x"}]))
        if args[:2] == ["git", "rev-parse"]:
            rev_parse_n["n"] += 1
            sha = "bbbbbbbb\n" if rev_parse_n["n"] == 1 else "cccccccc\n"
            return _ok(stdout=sha)
        return _ok()

    def fake_fdx(*a, **k):
        captured.update(k)
        return 0

    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.next_patch_from_tags",
        lambda repo=None: "v0.0.2",
    )
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.run_ci_fdx_diff",
        fake_fdx,
    )
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.build_release_notes",
        lambda *a, **k: "## Release v0.0.2\n",
    )

    rc = run_ci_daily_release(
        repo=tmp_path,
        token="tok",
        run=fake_run,
        write_actions_output=False,
        append_step_summary=False,
    )
    assert rc == 0
    assert captured.get("list_items") is True
    assert captured.get("display_boards") is True


def test_run_ci_daily_release_requires_token(tmp_path, monkeypatch):
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(
        "schoonmaker.ci_daily_release.shutil.which",
        lambda name: "/usr/bin/gh",
    )
    rc = run_ci_daily_release(
        repo=tmp_path,
        token=None,
        write_actions_output=False,
        append_step_summary=False,
    )
    assert rc == 1


def test_cli_ci_daily_release_help():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-daily-release", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
    assert "release-ready" in r.stdout or "label" in r.stdout
    assert DEFAULT_LABEL


def test_cli_args_ci_daily_release():
    from schoonmaker.cli_arg_parser import CLIArgParser

    args = CLIArgParser().parser.parse_args(
        [
            "ci-daily-release",
            "--label",
            "ship-it",
            "--default-branch",
            "main",
            "--merge-method",
            "merge",
        ]
    )
    assert args.command == "ci-daily-release"
    assert args.label == "ship-it"
    assert args.default_branch == "main"
    assert args.merge_method == "merge"
