"""Select exactly one labeled open PR for daily auto-release (pure logic)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


class SelectPrError(ValueError):
    """Invalid or ambiguous PR selection input."""


def select_exactly_one_pr(
    prs: list[dict[str, Any]],
    *,
    label: str | None = None,
) -> dict[str, Any]:
    """
    Return the single PR dict when ``prs`` has length 1.

    Raises ``SelectPrError`` when empty or when more than one PR is present.
    ``label`` is only used in error messages (filtering is the caller's job).
    """
    if not isinstance(prs, list):
        raise SelectPrError("expected a JSON array of pull requests")
    label_bit = f" with label {label!r}" if label else ""
    if len(prs) == 0:
        raise SelectPrError(f"no open pull requests{label_bit}")
    if len(prs) > 1:
        nums = []
        for p in prs:
            if isinstance(p, dict) and "number" in p:
                nums.append(str(p["number"]))
            else:
                nums.append("?")
        joined = ", ".join(nums)
        raise SelectPrError(
            f"expected exactly one open pull request{label_bit}; "
            f"found {len(prs)}: {joined}"
        )
    only = prs[0]
    if not isinstance(only, dict):
        raise SelectPrError("pull request entry must be an object")
    if "number" not in only:
        raise SelectPrError("pull request object missing 'number'")
    return only


def append_github_output(path: str | Path, values: dict[str, str]) -> None:
    """Append key=value rows for Actions ``GITHUB_OUTPUT``."""
    p = Path(path)
    with p.open("a", encoding="utf-8") as f:
        for key, val in values.items():
            text = "" if val is None else str(val)
            if "\n" in text:
                f.write(f"{key}<<EOF\n{text}\nEOF\n")
            else:
                f.write(f"{key}={text}\n")


def github_output_from_pr(pr: dict[str, Any]) -> dict[str, str]:
    """Map a selected PR object to Actions output keys."""
    return {
        "skip": "false",
        "pr_number": str(pr["number"]),
        "pr_title": str(pr.get("title") or ""),
        "pr_url": str(pr.get("url") or ""),
        "base_sha": str(pr.get("baseRefOid") or ""),
    }


def main_ci_select_pr(args: Any) -> int:
    """
    CLI entry for ``ci-select-pr``.

    Reads a JSON array of PR objects from stdin (e.g. ``gh pr list --json …``).
    On success prints the selected PR as JSON to stdout.
    Exit 0 when exactly one PR; exit 2 when none (unless ``--allow-empty``);
    exit 1 on error / ambiguity.
    """
    label = getattr(args, "label", None) or None
    allow_empty = bool(getattr(args, "allow_empty", False))
    actions_output = bool(getattr(args, "actions_output", False))
    json_out = getattr(args, "json_out", None)
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else []
    except json.JSONDecodeError as e:
        print(f"ci-select-pr: invalid JSON: {e}", file=sys.stderr)
        return 1
    try:
        selected = select_exactly_one_pr(data, label=label)
    except SelectPrError as e:
        msg = str(e)
        print(f"ci-select-pr: {msg}", file=sys.stderr)
        if msg.startswith("no open pull requests"):
            if allow_empty:
                if actions_output:
                    out = os.environ.get("GITHUB_OUTPUT")
                    if not out:
                        print(
                            "ci-select-pr: GITHUB_OUTPUT is unset",
                            file=sys.stderr,
                        )
                        return 1
                    append_github_output(out, {"skip": "true"})
                return 0
            return 2
        return 1

    if json_out:
        Path(json_out).write_text(
            json.dumps(selected, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    if actions_output:
        out = os.environ.get("GITHUB_OUTPUT")
        if not out:
            print("ci-select-pr: GITHUB_OUTPUT is unset", file=sys.stderr)
            return 1
        append_github_output(out, github_output_from_pr(selected))
    sys.stdout.write(json.dumps(selected, ensure_ascii=False) + "\n")
    return 0
