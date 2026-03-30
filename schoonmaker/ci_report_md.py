"""Markdown from ``ci-fdx-diff`` reports for GitHub Actions Step Summary."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _load_path_index(reports_dir: Path) -> dict[str, str]:
    """Map fingerprint to repo path using ``path-index.tsv`` columns."""
    p = reports_dir / "path-index.tsv"
    if not p.is_file():
        return {}
    out: dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or "\t" not in line:
            continue
        safe, rel = line.split("\t", 1)
        safe, rel = safe.strip(), rel.strip()
        if safe:
            out[safe] = rel
    return out


def _safe_from_diff_name(path: Path) -> str:
    """``ab12...-diff.json`` → ``ab12...``."""
    name = path.name
    if name.endswith("-diff.json"):
        return name[: -len("-diff.json")]
    return path.stem


def _fmt_changed_indices(indices: list[int], *, limit: int = 24) -> str:
    if not indices:
        return "—"
    if len(indices) <= limit:
        return ", ".join(str(i) for i in indices)
    head = ", ".join(str(i) for i in indices[:limit])
    return f"{head}, … (+{len(indices) - limit} more)"


def _render_one_diff(data: dict[str, Any], title: str) -> str:
    lines: list[str] = []
    lines.append(f"### {title}")
    lines.append("")

    sc = data.get("scenes") or {}
    if isinstance(sc, dict):
        lines.append("| (scenes) | Before | After | Δ |")
        lines.append("| --- | ---: | ---: | ---: |")
        cb, ca = sc.get("count_before"), sc.get("count_after")
        delta_n = (ca or 0) - (cb or 0)
        lines.append(f"| Scene count | {cb} | {ca} | {delta_n:+d} |")
        changed_idx = sc.get("changed_indices") or []
        if isinstance(changed_idx, list) and changed_idx:
            nums = [int(x) for x in changed_idx if isinstance(x, (int, float))]
            lines.append("")
            cj = _fmt_changed_indices(nums)
            lines.append(f"**Changed scene indices:** {cj}")
        added = sc.get("added_scene_indices") or []
        rem = sc.get("removed_scene_indices") or []
        if (isinstance(added, list) and added) or (
            isinstance(rem, list) and rem
        ):
            lines.append("")
            if added:
                add_nums = [
                    int(x) for x in added if isinstance(x, (int, float))
                ]
                aj = _fmt_changed_indices(add_nums, limit=16)
                lines.append(f"**Added scenes (indices):** {aj}")
            if rem:
                rem_nums = [int(x) for x in rem if isinstance(x, (int, float))]
                rj = _fmt_changed_indices(rem_nums, limit=16)
                lines.append(f"**Removed scenes (indices):** {rj}")

    counts = data.get("counts") or {}
    tw = counts.get("total_words") if isinstance(counts, dict) else None
    if isinstance(tw, dict):
        b, a, d = tw.get("before"), tw.get("after"), tw.get("delta")
        lines.append("")
        lines.append("| Words | Before | After | Δ |")
        lines.append("| --- | ---: | ---: | ---: |")
        if isinstance(d, int):
            line = f"| Total | {b} | {a} | {d:+d} |"
        else:
            line = f"| Total | {b} | {a} | |"
        lines.append(line)

    chars = data.get("characters") or {}
    if isinstance(chars, dict):
        n_new = len(chars.get("new") or [])
        n_gone = len(chars.get("removed") or [])
        n_ch = len(chars.get("changed") or [])
        if n_new or n_gone or n_ch:
            lines.append("")
            lines.append(
                "**Characters:** "
                f"{n_new} new, {n_gone} removed, {n_ch} changed"
            )

    for key in ("list_items", "display_boards"):
        blk = data.get(key)
        if isinstance(blk, dict) and blk:
            chg = blk.get("changed")
            cb, ca = blk.get("count_before"), blk.get("count_after")
            lines.append("")
            lines.append(
                f"**{key}:** counts {cb} → {ca}"
                + (
                    f", **changed:** {'yes' if chg else 'no'}"
                    if chg is not None
                    else ""
                )
            )

    warns = data.get("warnings") or []
    if isinstance(warns, list) and warns:
        lines.append("")
        lines.append("**Warnings**")
        for w in warns:
            if isinstance(w, str) and w.strip():
                lines.append(f"- {w.strip()}")

    lines.append("")
    return "\n".join(lines)


def markdown_from_ci_reports(reports_dir: str | Path) -> str:
    """
    Build Markdown for GitHub Step Summary from ``*-diff.json`` files.

    Uses ``path-index.tsv`` in the same directory to label each file with the
    repo-relative ``.fdx`` path when present.
    """
    root = Path(reports_dir).resolve()
    index = _load_path_index(root)
    diff_files = sorted(root.glob("*-diff.json"))
    if not diff_files:
        return (
            "## FDX diff report\n\n"
            "_No `*-diff.json` files in this directory._\n"
        )

    parts: list[str] = ["## FDX diff report\n"]
    for df in diff_files:
        try:
            data = json.loads(df.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            parts.append(f"### {df.name}\n\n_Parse error: {e}_\n\n")
            continue
        if not isinstance(data, dict):
            parts.append(f"### {df.name}\n\n_Invalid JSON root._\n\n")
            continue
        safe = _safe_from_diff_name(df)
        title = index.get(safe) or df.name
        parts.append(_render_one_diff(data, title))
    return "".join(parts)


def main_ci_report_md(args: Any) -> int:
    """CLI entry for ``ci-report-md``."""
    d = getattr(args, "reports_dir", None) or "."
    md = markdown_from_ci_reports(d)
    out = getattr(args, "output", None)
    if out:
        Path(out).write_text(md, encoding="utf-8")
    else:
        sys.stdout.write(md)
        if not md.endswith("\n"):
            sys.stdout.write("\n")
    return 0
