"""CLI for ``next-semver`` (patch bump / latest tag)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from schoonmaker.semver_util import (
    bump_patch,
    latest_semver_tag,
    next_patch_from_tags,
)


def main_next_semver(args: Any) -> int:
    """
    Print the next patch version.

    Modes:
    - ``VERSION`` positional: bump that string.
    - ``--from-tags``: bump after latest semver git tag (or ``--default``).
    - ``--latest-tag``: print latest tag only (no bump).
    """
    version = getattr(args, "version", None)
    from_tags = bool(getattr(args, "from_tags", False))
    latest_only = bool(getattr(args, "latest_tag", False))
    default = getattr(args, "default", None) or "v0.0.0"
    repo_arg = getattr(args, "repo", None)
    repo = None
    if repo_arg is not None and str(repo_arg).strip():
        repo = Path(str(repo_arg)).resolve()

    if latest_only and from_tags:
        print(
            "next-semver: use only one of --latest-tag / --from-tags",
            file=sys.stderr,
        )
        return 1
    if latest_only and version:
        print(
            "next-semver: do not pass VERSION with --latest-tag",
            file=sys.stderr,
        )
        return 1
    if from_tags and version:
        print(
            "next-semver: do not pass VERSION with --from-tags",
            file=sys.stderr,
        )
        return 1
    if not latest_only and not from_tags and not version:
        print(
            "next-semver: pass VERSION, or --from-tags / --latest-tag",
            file=sys.stderr,
        )
        return 1

    try:
        if latest_only:
            tag = latest_semver_tag(repo=repo)
            if tag is None:
                print("next-semver: no semver tags found", file=sys.stderr)
                return 1
            out = tag
        elif from_tags:
            out = next_patch_from_tags(repo=repo, default=default)
        else:
            out = bump_patch(str(version))
    except (ValueError, RuntimeError) as e:
        print(f"next-semver: {e}", file=sys.stderr)
        return 1

    sys.stdout.write(out + "\n")
    return 0
