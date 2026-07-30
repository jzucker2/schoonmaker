"""Semver helpers for CI patch releases (stdlib only)."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_SEMVER_RE = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
)


def parse_semver(text: str) -> tuple[int, int, int]:
    """
    Parse ``MAJOR.MINOR.PATCH`` (optional leading ``v``).

    Pre-release / build metadata are accepted but ignored for bumping.
    """
    s = (text or "").strip()
    m = _SEMVER_RE.match(s)
    if not m:
        raise ValueError(f"not a semver version: {text!r}")
    return int(m.group("major")), int(m.group("minor")), int(m.group("patch"))


def format_semver(
    major: int,
    minor: int,
    patch: int,
    *,
    prefix_v: bool = True,
) -> str:
    """Format a version triple; ``prefix_v`` adds a leading ``v``."""
    body = f"{major}.{minor}.{patch}"
    return f"v{body}" if prefix_v else body


def bump_patch(version: str, *, prefix_v: bool | None = None) -> str:
    """
    Return the next patch version.

    If ``prefix_v`` is None, keep a leading ``v`` iff ``version`` had one.
    """
    major, minor, patch = parse_semver(version)
    had_v = version.strip().startswith("v") or version.strip().startswith("V")
    use_v = had_v if prefix_v is None else prefix_v
    return format_semver(major, minor, patch + 1, prefix_v=use_v)


def _git_tag_list(repo: Path | None) -> list[str]:
    r = subprocess.run(
        ["git", "tag", "-l"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
        encoding="utf-8",
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "git tag failed").strip()
        raise RuntimeError(err)
    return [ln.strip() for ln in (r.stdout or "").splitlines() if ln.strip()]


def latest_semver_tag(
    tags: list[str] | None = None,
    *,
    repo: Path | None = None,
) -> str | None:
    """
    Highest semver among tags (or ``git tag -l`` when ``tags`` is None).

    Non-semver tags are ignored. Returns the tag as stored (keeps ``v``).
    """
    if tags is None:
        tags = _git_tag_list(repo)
    best: tuple[int, int, int] | None = None
    best_tag: str | None = None
    for tag in tags:
        try:
            triple = parse_semver(tag)
        except ValueError:
            continue
        if best is None or triple > best:
            best = triple
            best_tag = tag
    return best_tag


def next_patch_from_tags(
    tags: list[str] | None = None,
    *,
    repo: Path | None = None,
    default: str = "v0.0.0",
) -> str:
    """
    Next patch after the latest semver tag, or bump ``default`` if none.

    ``default`` is usually ``v0.0.0`` so the first release is ``v0.0.1``.
    """
    latest = latest_semver_tag(tags, repo=repo)
    return bump_patch(latest if latest is not None else default)
