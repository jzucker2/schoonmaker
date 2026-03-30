"""
CI helper: diff changed .fdx files between two commits (e.g. GitHub Actions).

Used by ``schoonmaker ci-fdx-diff``; orchestration lives here for unit tests.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


# git push event uses this when there is no parent (new branch, etc.)
_GIT_NULL_SHA = "0" * 40


def path_fingerprint(repo_relative_path: str) -> str:
    """Stable hex id for a repo path (like diff report artifact names)."""
    return hashlib.sha256(repo_relative_path.encode("utf-8")).hexdigest()


def _git(
    args: list[str],
    *,
    cwd: Path | None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
        encoding="utf-8",
    )


def resolve_base_sha(
    base_sha: str,
    head_sha: str,
    repo: Path | None = None,
) -> str | None:
    """
    Effective base for diffing.

    If ``base_sha`` is empty or all zeros (GitHub push payload), use
    ``head_sha^`` when it exists; otherwise None (caller should skip).
    """
    b = (base_sha or "").strip()
    h = (head_sha or "").strip()
    if not h:
        return None
    if b and b != _GIT_NULL_SHA:
        return b
    r = _git(["rev-parse", "--verify", f"{h}^"], cwd=repo, check=False)
    if r.returncode == 0:
        out = (r.stdout or "").strip()
        return out or None
    return None


def list_changed_fdx_paths(
    base_sha: str,
    head_sha: str,
    repo: Path | None = None,
) -> list[str]:
    """Paths of .fdx files changed between commits (POSIX-style paths)."""
    r = _git(
        [
            "diff",
            "--name-only",
            base_sha,
            head_sha,
            "--",
            "*.fdx",
            "*.FDX",
        ],
        cwd=repo,
        check=False,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"git diff failed: {r.stderr or r.stdout or 'no output'}"
        )
    lines = [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]
    return [ln.replace("\\", "/") for ln in lines]


def run_ci_fdx_diff(
    output_dir: Path,
    base_sha: str,
    head_sha: str,
    *,
    repo: Path | None = None,
) -> int:
    """
    For each changed .fdx between base and head: parse both, write diff JSON.

    Returns 0 on success, 1 on error, or 0 if skipped (no head or no base).
    """
    cwd = repo
    h = (head_sha or "").strip()
    if not h:
        print("ci-fdx-diff: head SHA is required", file=sys.stderr)
        return 1

    resolved_base = resolve_base_sha(base_sha, h, repo=cwd)
    if not resolved_base:
        print(
            "ci-fdx-diff: no base commit to compare; skip.",
            file=sys.stderr,
        )
        return 0

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    index_path = output_dir / "path-index.tsv"
    index_path.write_text("", encoding="utf-8")

    try:
        paths = list_changed_fdx_paths(resolved_base, h, repo=cwd)
    except RuntimeError as e:
        print(f"ci-fdx-diff: {e}", file=sys.stderr)
        return 1

    if not paths:
        print("No .fdx files in this diff.")
        return 0

    tmp_root = output_dir / "_tmp"
    tmp_root.mkdir(exist_ok=True)
    try:
        return _run_ci_fdx_diff_loop(
            paths,
            resolved_base,
            h,
            cwd,
            output_dir,
            tmp_root,
        )
    finally:
        if tmp_root.exists():
            shutil.rmtree(tmp_root, ignore_errors=True)


def _run_ci_fdx_diff_loop(
    paths: list[str],
    resolved_base: str,
    head_sha: str,
    cwd: Path | None,
    output_dir: Path,
    tmp_root: Path,
) -> int:
    from schoonmaker.cli import run_diff, run_parse

    index_path = output_dir / "path-index.tsv"
    for rel in paths:
        safe = path_fingerprint(rel)
        with index_path.open("a", encoding="utf-8") as idx:
            idx.write(f"{safe}\t{rel}\n")

        before_fdx = tmp_root / f"before_{safe}.fdx"
        r_show = _git(["show", f"{resolved_base}:{rel}"], cwd=cwd, check=False)
        has_before = r_show.returncode == 0 and (r_show.stdout is not None)
        if has_before:
            before_fdx.write_text(r_show.stdout, encoding="utf-8")
        else:
            if before_fdx.exists():
                before_fdx.unlink()

        r_head = _git(
            ["cat-file", "-e", f"{head_sha}:{rel}"],
            cwd=cwd,
            check=False,
        )
        if r_head.returncode != 0:
            deleted = output_dir / f"{safe}-deleted.txt"
            deleted.write_text(f"Deleted: {rel}\n", encoding="utf-8")
            continue

        r_after = _git(["show", f"{head_sha}:{rel}"], cwd=cwd, check=False)
        if r_after.returncode != 0:
            msg = f"ci-fdx-diff: could not read {rel} at head"
            print(msg, file=sys.stderr)
            return 1
        after_fdx = tmp_root / f"after_{safe}.fdx"
        after_fdx.write_text(r_after.stdout or "", encoding="utf-8")

        before_json = tmp_root / f"before_{safe}.json"
        after_json = tmp_root / f"after_{safe}.json"
        diff_out = output_dir / f"{safe}-diff.json"

        if has_before:
            rc = run_parse(
                SimpleNamespace(
                    command="parse",
                    file=str(before_fdx),
                    output=str(before_json),
                    metadata=True,
                    checksum=True,
                    file_info=False,
                )
            )
            if rc != 0:
                return rc
            rc = run_parse(
                SimpleNamespace(
                    command="parse",
                    file=str(after_fdx),
                    output=str(after_json),
                    metadata=True,
                    checksum=True,
                    file_info=False,
                )
            )
            if rc != 0:
                return rc
            rc = run_diff(
                SimpleNamespace(
                    command="diff",
                    before=str(before_json),
                    after=str(after_json),
                    output=str(diff_out),
                )
            )
            if rc != 0:
                return rc
        else:
            new_note = output_dir / f"{safe}-new.txt"
            new_note.write_text(f"New file: {rel}\n", encoding="utf-8")
            parse_only = output_dir / f"{safe}-parse.json"
            rc = run_parse(
                SimpleNamespace(
                    command="parse",
                    file=str(after_fdx),
                    output=str(parse_only),
                    metadata=True,
                    checksum=True,
                    file_info=False,
                )
            )
            if rc != 0:
                return rc

    return 0


def main_ci_fdx_diff(args: SimpleNamespace) -> int:
    """Entry for ``ci-fdx-diff`` subcommand."""
    out = Path(args.output)
    base = getattr(args, "base_sha", "") or os.environ.get(
        "CI_FDX_BASE_SHA", ""
    )
    head = getattr(args, "head_sha", "") or os.environ.get(
        "CI_FDX_HEAD_SHA", ""
    )
    repo_arg = getattr(args, "repo", None)
    repo = None
    if repo_arg is not None and str(repo_arg).strip():
        repo = Path(str(repo_arg)).resolve()
    return run_ci_fdx_diff(out, base, head, repo=repo)
