"""
Auto-label a PR when its head branch matches a prefix (daily release prep).

Used by ``schoonmaker ci-label-pr`` (see examples workflow). Requires ``gh``
on PATH and ``GH_TOKEN`` (or ``GITHUB_TOKEN``) unless ``--dry-run``.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Any, Callable

from schoonmaker.ci_select_pr import append_github_output


DEFAULT_LABEL = "release-ready"
DEFAULT_BRANCH_PREFIX = "writing/"

RunFn = Callable[..., subprocess.CompletedProcess[str]]


def should_label_pr(head_ref: str, branch_prefix: str) -> bool:
    """
    Return True when ``head_ref`` should get the daily-release label.

    Matching is a case-sensitive prefix check:
    ``head_ref.startswith(branch_prefix)`` after stripping both strings.
    An empty prefix (after strip) never matches, so a misconfigured empty
    env value does not label every PR.
    """
    ref = (head_ref or "").strip()
    prefix = (branch_prefix or "").strip()
    if not ref or not prefix:
        return False
    return ref.startswith(prefix)


def _default_run(
    args: list[str],
    *,
    cwd=None,
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


def _resolve_head_ref(explicit: str | None) -> str:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    for key in ("PR_HEAD_REF", "GITHUB_HEAD_REF"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return ""


def _resolve_pr_number(explicit: str | int | None) -> str:
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    for key in ("PR_NUMBER",):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return ""


def _write_labeled_output(labeled: bool) -> int | None:
    """
    Append ``labeled=true|false`` to ``GITHUB_OUTPUT`` when set.

    Returns 1 if ``GITHUB_OUTPUT`` is required but unset/unwritable;
    otherwise None (caller continues).
    """
    out = os.environ.get("GITHUB_OUTPUT")
    if not out:
        return None
    try:
        append_github_output(out, {"labeled": "true" if labeled else "false"})
    except OSError as e:
        print(f"ci-label-pr: GITHUB_OUTPUT write failed: {e}", file=sys.stderr)
        return 1
    return None


def run_ci_label_pr(
    *,
    pr_number: str | int | None = None,
    head_ref: str | None = None,
    label: str = DEFAULT_LABEL,
    branch_prefix: str = DEFAULT_BRANCH_PREFIX,
    dry_run: bool = False,
    token: str | None = None,
    write_actions_output: bool = True,
    run: RunFn | None = None,
) -> int:
    """
    If the PR head branch matches ``branch_prefix``, add ``label`` via ``gh``.

    Returns 0 on success, skip (no match), or dry-run. Returns 1 on error.
    Idempotent: ``gh pr edit --add-label`` when the label is already present
    is treated as success.
    """
    run_fn = run or _default_run
    ref = _resolve_head_ref(head_ref)
    pr = _resolve_pr_number(pr_number)
    label_s = (label or DEFAULT_LABEL).strip() or DEFAULT_LABEL
    prefix = (branch_prefix or DEFAULT_BRANCH_PREFIX).strip()
    if not prefix:
        prefix = DEFAULT_BRANCH_PREFIX

    if not ref:
        print(
            "ci-label-pr: head ref required "
            "(--head-ref or PR_HEAD_REF / GITHUB_HEAD_REF)",
            file=sys.stderr,
        )
        return 1
    if not pr:
        print(
            "ci-label-pr: PR number required (--pr or PR_NUMBER)",
            file=sys.stderr,
        )
        return 1

    if not should_label_pr(ref, prefix):
        print(
            f"ci-label-pr: head ref {ref!r} does not start with "
            f"prefix {prefix!r}; skipping",
            file=sys.stderr,
        )
        if write_actions_output:
            err = _write_labeled_output(False)
            if err is not None:
                return err
        return 0

    if dry_run:
        print(
            f"ci-label-pr: dry-run; would add label {label_s!r} "
            f"to PR #{pr} (head {ref!r})"
        )
        if write_actions_output:
            err = _write_labeled_output(True)
            if err is not None:
                return err
        return 0

    tok = _resolve_token(token)
    if not tok:
        print(
            "ci-label-pr: GH_TOKEN or GITHUB_TOKEN is required",
            file=sys.stderr,
        )
        return 1
    if shutil.which("gh") is None:
        print("ci-label-pr: gh CLI not found on PATH", file=sys.stderr)
        return 1

    gh_env = _gh_env(tok)
    try:
        run_fn(
            ["gh", "pr", "edit", str(pr), "--add-label", label_s],
            check=True,
            env=gh_env,
        )
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or str(e)).strip()
        print(f"ci-label-pr: add label failed: {err}", file=sys.stderr)
        return 1

    print(f"ci-label-pr: added label {label_s!r} to PR #{pr}")
    if write_actions_output:
        err = _write_labeled_output(True)
        if err is not None:
            return err
    return 0


def main_ci_label_pr(args: Any) -> int:
    """CLI entry for ``ci-label-pr``."""
    label = getattr(args, "label", None) or os.environ.get(
        "RELEASE_LABEL", DEFAULT_LABEL
    )
    prefix = getattr(args, "branch_prefix", None) or os.environ.get(
        "PR_BRANCH_PREFIX", DEFAULT_BRANCH_PREFIX
    )
    head = getattr(args, "head_ref", None) or None
    pr = getattr(args, "pr_number", None) or None
    dry_run = bool(getattr(args, "dry_run", False))
    return run_ci_label_pr(
        pr_number=pr,
        head_ref=head,
        label=str(label),
        branch_prefix=str(prefix),
        dry_run=dry_run,
        write_actions_output=not bool(
            getattr(args, "no_actions_output", False)
        ),
    )
