"""Tests for ``ci-report-md`` Markdown rendering."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from schoonmaker.ci_report_md import markdown_from_ci_reports
from schoonmaker.ci_fdx_diff import path_fingerprint
from schoonmaker.parse_json_diff import build_diff_report


def test_markdown_from_ci_reports_empty_dir(tmp_path):
    md = markdown_from_ci_reports(tmp_path)
    assert "No `*-diff.json`" in md


def test_markdown_uses_path_index_and_scenes(
    sample_fdx_path,
    tmp_path,
):
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    from schoonmaker.cli import run_parse

    for out in (ja, jb):
        args = SimpleNamespace(
            command="parse",
            file=str(sample_fdx_path),
            output=str(out),
            metadata=True,
            checksum=True,
            file_info=False,
            list_items=False,
            display_boards=False,
        )
        run_parse(args)
    da = json.loads(ja.read_text(encoding="utf-8"))
    db = json.loads(jb.read_text(encoding="utf-8"))
    rep = build_diff_report(da, db, label_a="before", label_b="after")
    rel = "Scripts/my.fdx"
    safe = path_fingerprint(rel)
    diff_path = tmp_path / f"{safe}-diff.json"
    diff_path.write_text(
        json.dumps(rep, ensure_ascii=False),
        encoding="utf-8",
    )
    (tmp_path / "path-index.tsv").write_text(
        f"{safe}\t{rel}\n", encoding="utf-8"
    )
    md = markdown_from_ci_reports(tmp_path)
    assert rel in md
    assert "Scene count" in md


def test_cli_ci_report_md_help():
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "ci-report-md", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
