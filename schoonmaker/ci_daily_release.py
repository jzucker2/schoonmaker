"""
Daily auto-release: merge labeled PR, patch GitHub Release, FDX report.

Used by ``schoonmaker ci-daily-release`` (see examples workflow). Requires
``gh`` and ``git`` on PATH and ``GH_TOKEN`` (or ``GITHUB_TOKEN``) in the env.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from schoonmaker.ci_fdx_diff import _env_truthy, run_ci_fdx_diff
from schoonmaker.ci_release_notes import build_release_notes
from schoonmaker.ci_select_pr import (
    SelectPrError,
    append_github_output,
    github_output_from_pr,
    select_exactly_one_pr,
)
from schoonmaker.semver_util import next_patch_from_tags


DEFAULT_LABEL = "release-ready"
DEFAULT_BRANCH = "master"
DEFAULT_REPORTS_DIR = "fdx-reports"
DEFAULT_NOTES_FILE = "RELEASE_NOTES.md"
DEFAULT_MERGE_METHOD = "squash"

RunFn = Callable[..., subprocess.CompletedProcess[str]]


def _default_run(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        encoding="utf-8",
        env=env,
        input=input_text,
    )


def _resolve_token(explicit: str | None = None) -> str | None:
    if explicit and explicit.strip():
        return explicit.strip()
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return None


def _gh_env(token: str) -> dict[str, str]:
    env = dict(os.environ)
    env["GH_TOKEN"] = token
    env["GITHUB_TOKEN"] = token
    return env


def run_ci_daily_release(
    *,
    label: str = DEFAULT_LABEL,
    default_branch: str = DEFAULT_BRANCH,
    reports_dir: str | Path = DEFAULT_REPORTS_DIR,
    notes_file: str | Path = DEFAULT_NOTES_FILE,
    repo: Path | None = None,
    merge_method: str = DEFAULT_MERGE_METHOD,
    token: str | None = None,
    write_actions_output: bool = True,
    append_step_summary: bool = True,
    run: RunFn | None = None,
) -> int:
    """
    Select one open PR with ``label``, squash-merge (default), patch-tag,
    ``ci-fdx-diff``, release notes, ``gh release create``, PR comment.

    Returns 0 on success or skip (no labeled PR). Returns 1 on error.
    """
    run_fn = run or _default_run
    cwd = repo.resolve() if repo is not None else Path.cwd()
    reports = Path(reports_dir)
    if not reports.is_absolute():
        reports = cwd / reports
    notes = Path(notes_file)
    if not notes.is_absolute():
        notes = cwd / notes

    tok = _resolve_token(token)
    if not tok:
        print(
            "ci-daily-release: GH_TOKEN or GITHUB_TOKEN is required",
            file=sys.stderr,
        )
        return 1
    if shutil.which("gh") is None:
        print("ci-daily-release: gh CLI not found on PATH", file=sys.stderr)
        return 1

    method = (merge_method or DEFAULT_MERGE_METHOD).strip().lower()
    if method not in ("squash", "merge", "rebase"):
        print(
            f"ci-daily-release: invalid merge method {merge_method!r}",
            file=sys.stderr,
        )
        return 1

    gh_env = _gh_env(tok)
    label = (label or DEFAULT_LABEL).strip() or DEFAULT_LABEL
    branch = (default_branch or DEFAULT_BRANCH).strip() or DEFAULT_BRANCH

    print(f"==> Listing open PRs with label {label} (base {branch})")
    try:
        listed = run_fn(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--label",
                label,
                "--base",
                branch,
                "--json",
                "number,title,url",
            ],
            cwd=cwd,
            check=True,
            env=gh_env,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-daily-release: gh pr list failed: {err}", file=sys.stderr)
        return 1

    try:
        prs = json.loads(listed.stdout or "[]")
    except json.JSONDecodeError as e:
        print(f"ci-daily-release: invalid gh JSON: {e}", file=sys.stderr)
        return 1

    ghub_out = (
        os.environ.get("GITHUB_OUTPUT") if write_actions_output else None
    )
    try:
        selected = select_exactly_one_pr(prs, label=label)
    except SelectPrError as e:
        msg = str(e)
        if msg.startswith("no open pull requests"):
            print(f"No open PR with label {label}; skipping.")
            if ghub_out:
                append_github_output(ghub_out, {"skip": "true"})
            return 0
        print(f"ci-daily-release: {msg}", file=sys.stderr)
        return 1

    if ghub_out:
        append_github_output(ghub_out, github_output_from_pr(selected))

    pr_number = int(selected["number"])
    pr_title = str(selected.get("title") or "")
    pr_url = str(selected.get("url") or "")

    merge_flag = {
        "squash": "--squash",
        "merge": "--merge",
        "rebase": "--rebase",
    }[method]

    # Capture default-branch tip *before* merge so the FDX report is exactly
    # the delta introduced by this merge (not a possibly stale baseRefOid).
    print(f"==> Recording pre-merge tip of {branch}")
    try:
        run_fn(
            ["git", "fetch", "origin", branch, "--tags"],
            cwd=cwd,
            check=True,
        )
        base_proc = run_fn(
            ["git", "rev-parse", f"origin/{branch}"],
            cwd=cwd,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(
            f"ci-daily-release: pre-merge fetch failed: {err}",
            file=sys.stderr,
        )
        return 1
    base_sha = (base_proc.stdout or "").strip()
    if not base_sha:
        print(
            f"ci-daily-release: empty origin/{branch} before merge",
            file=sys.stderr,
        )
        return 1

    print(f"==> Merging PR #{pr_number} ({method})")
    try:
        run_fn(
            [
                "gh",
                "pr",
                "merge",
                str(pr_number),
                merge_flag,
                "--delete-branch=false",
            ],
            cwd=cwd,
            check=True,
            env=gh_env,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-daily-release: merge failed: {err}", file=sys.stderr)
        return 1

    print(f"==> Syncing {branch} and choosing next patch tag")
    try:
        run_fn(
            ["git", "fetch", "origin", branch, "--tags"],
            cwd=cwd,
            check=True,
        )
        run_fn(["git", "checkout", branch], cwd=cwd, check=True)
        run_fn(
            ["git", "reset", "--hard", f"origin/{branch}"],
            cwd=cwd,
            check=True,
        )
        head = run_fn(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-daily-release: git sync failed: {err}", file=sys.stderr)
        return 1

    head_sha = (head.stdout or "").strip()
    if not head_sha:
        print("ci-daily-release: empty HEAD after sync", file=sys.stderr)
        return 1

    try:
        tag = next_patch_from_tags(repo=cwd)
    except RuntimeError as e:
        print(f"ci-daily-release: {e}", file=sys.stderr)
        return 1

    if ghub_out:
        append_github_output(
            ghub_out,
            {
                "base_sha": base_sha,
                "head_sha": head_sha,
                "tag": tag,
            },
        )

    print(f"==> FDX diff {base_sha[:7]}..{head_sha[:7]}")
    rc = run_ci_fdx_diff(
        reports,
        base_sha,
        head_sha,
        repo=cwd,
        list_items=_env_truthy("CI_FDX_LIST_ITEMS"),
        display_boards=_env_truthy("CI_FDX_DISPLAY_BOARDS"),
    )
    if rc != 0:
        return rc

    print(f"==> Building release notes {notes}")
    md = build_release_notes(
        reports,
        version=tag,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_url=pr_url,
    )
    notes.write_text(md, encoding="utf-8")

    if append_step_summary:
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            # Release notes already embed the FDX Markdown report.
            with Path(summary).open("a", encoding="utf-8") as f:
                f.write(md)
                if not md.endswith("\n"):
                    f.write("\n")

    print(f"==> Creating GitHub Release {tag}")
    try:
        run_fn(
            [
                "gh",
                "release",
                "create",
                tag,
                "--target",
                head_sha,
                "--title",
                tag,
                "--notes-file",
                str(notes),
            ],
            cwd=cwd,
            check=True,
            env=gh_env,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-daily-release: release failed: {err}", file=sys.stderr)
        return 1

    print(f"==> Commenting on PR #{pr_number}")
    try:
        run_fn(
            [
                "gh",
                "pr",
                "comment",
                str(pr_number),
                "--body-file",
                str(notes),
            ],
            cwd=cwd,
            check=True,
            env=gh_env,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-daily-release: PR comment failed: {err}", file=sys.stderr)
        return 1

    print(f"Done: released {tag} from PR #{pr_number}")
    return 0


def main_ci_daily_release(args: Any) -> int:
    """CLI entry for ``ci-daily-release``."""
    label = getattr(args, "label", None) or os.environ.get(
        "RELEASE_LABEL", DEFAULT_LABEL
    )
    branch = getattr(args, "default_branch", None) or os.environ.get(
        "DEFAULT_BRANCH", DEFAULT_BRANCH
    )
    reports = getattr(args, "reports_dir", None) or DEFAULT_REPORTS_DIR
    notes = getattr(args, "notes_file", None) or DEFAULT_NOTES_FILE
    merge_method = getattr(args, "merge_method", None) or DEFAULT_MERGE_METHOD
    repo_arg = getattr(args, "repo", None)
    repo = None
    if repo_arg is not None and str(repo_arg).strip():
        repo = Path(str(repo_arg)).resolve()
    return run_ci_daily_release(
        label=str(label),
        default_branch=str(branch),
        reports_dir=reports,
        notes_file=notes,
        repo=repo,
        merge_method=str(merge_method),
        write_actions_output=not bool(
            getattr(args, "no_actions_output", False)
        ),
        append_step_summary=not bool(getattr(args, "no_step_summary", False)),
    )
