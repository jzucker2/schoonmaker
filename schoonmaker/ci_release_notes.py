"""Compose GitHub Release / PR comment Markdown from ci-fdx-diff reports."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from schoonmaker.ci_report_md import markdown_from_ci_reports


def build_release_notes(
    reports_dir: str | Path,
    *,
    version: str,
    pr_number: int | None = None,
    pr_title: str | None = None,
    pr_url: str | None = None,
    intro: str | None = None,
) -> str:
    """
    Markdown body for a patch release (and optional PR comment).

    Includes a short header plus ``markdown_from_ci_reports`` output.
    """
    ver = (version or "").strip()
    if not ver:
        raise ValueError("version is required")

    lines: list[str] = [f"## Release {ver}", ""]
    if intro and intro.strip():
        lines.append(intro.strip())
        lines.append("")

    if pr_number is not None:
        title_bit = ""
        if pr_title and pr_title.strip():
            title_bit = f": {pr_title.strip()}"
        if pr_url and pr_url.strip():
            lines.append(f"Merged [#{pr_number}]({pr_url.strip()}){title_bit}")
        else:
            lines.append(f"Merged #{pr_number}{title_bit}")
        lines.append("")

    report = markdown_from_ci_reports(reports_dir).rstrip()
    if report:
        lines.append(report)
        lines.append("")
    return "\n".join(lines)


def main_ci_release_notes(args: Any) -> int:
    """CLI entry for ``ci-release-notes``."""
    reports = getattr(args, "reports_dir", None) or "."
    version = getattr(args, "version", "") or ""
    pr_number = getattr(args, "pr_number", None)
    if pr_number is not None:
        pr_number = int(pr_number)
    try:
        md = build_release_notes(
            reports,
            version=version,
            pr_number=pr_number,
            pr_title=getattr(args, "pr_title", None),
            pr_url=getattr(args, "pr_url", None),
            intro=getattr(args, "intro", None),
        )
    except ValueError as e:
        print(f"ci-release-notes: {e}", file=sys.stderr)
        return 1
    out = getattr(args, "output", None)
    if out:
        Path(out).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
        if not md.endswith("\n"):
            sys.stdout.write("\n")
    return 0
