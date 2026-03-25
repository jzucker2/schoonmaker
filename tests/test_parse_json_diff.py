"""Tests for parse JSON diff (cli.py diff)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from schoonmaker.parse_json_diff import (
    build_diff_report,
    load_parse_json,
    scene_content_digest,
    scene_digests,
)


def _run_parse_json(out_path, fdx_path, **flags):
    from cli import run_parse

    a = type(
        "Args",
        (),
        {
            "command": "parse",
            "file": str(fdx_path),
            "output": str(out_path),
            "metadata": flags.get("metadata", False),
            "checksum": flags.get("checksum", False),
            "file_info": flags.get("file_info", False),
        },
    )()
    run_parse(a)


def test_scene_digest_matches_parse_scene_checksums(sample_fdx_path, tmp_path):
    """Recomputed scene digests match parse output when --checksum is used."""
    out = tmp_path / "p.json"
    _run_parse_json(out, sample_fdx_path, metadata=True, checksum=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    scenes = data["scenes"]
    stored = data["checksums"]["scene_checksums"]
    for i, scene in enumerate(scenes):
        assert scene_content_digest(scene, i) == stored[i]


def test_diff_identical_documents_empty_delta(sample_fdx_path, tmp_path):
    """Two parses of the same FDX show no scene or word deltas."""
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    _run_parse_json(ja, sample_fdx_path, metadata=True, checksum=True)
    _run_parse_json(jb, sample_fdx_path, metadata=True, checksum=True)
    r = build_diff_report(
        load_parse_json(ja),
        load_parse_json(jb),
    )
    assert r["scenes"]["changed_indices"] == []
    assert r["scenes"]["added_count"] == 0
    assert r["scenes"]["removed_count"] == 0
    assert r["counts"]["total_words"]["delta"] == 0
    assert r["characters"]["new"] == []
    assert r["characters"]["removed"] == []


def test_diff_detects_scene_heading_change(sample_fdx_path, tmp_path):
    """Mutating one scene heading yields that index in changed_indices."""
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    _run_parse_json(ja, sample_fdx_path, metadata=True, checksum=True)
    data = json.loads(ja.read_text(encoding="utf-8"))
    data["scenes"][0]["heading"]["raw"] = "INT. CHANGED LOCATION - DAY"
    jb.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    r = build_diff_report(
        load_parse_json(ja),
        load_parse_json(jb),
    )
    assert 0 in r["scenes"]["changed_indices"]


def test_diff_added_scene_in_after(sample_fdx_path, tmp_path):
    """Extra scene in ``after`` increases count and marks new tail index."""
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    _run_parse_json(ja, sample_fdx_path, metadata=True, checksum=True)
    data = json.loads(ja.read_text(encoding="utf-8"))
    dup = json.loads(json.dumps(data["scenes"][-1]))
    data["scenes"].append(dup)
    if "metadata" in data:
        del data["metadata"]
    if "checksums" in data:
        del data["checksums"]
    jb.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    r = build_diff_report(load_parse_json(ja), load_parse_json(jb))
    assert r["scenes"]["added_count"] == 1
    assert r["scenes"]["removed_count"] == 0
    n_before = r["scenes"]["count_before"]
    assert n_before + 1 == r["scenes"]["count_after"]


def test_diff_without_metadata_warns(sample_fdx_path, tmp_path):
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    _run_parse_json(ja, sample_fdx_path, metadata=False, checksum=True)
    _run_parse_json(jb, sample_fdx_path, metadata=False, checksum=True)
    r = build_diff_report(load_parse_json(ja), load_parse_json(jb))
    assert any("metadata" in w.lower() for w in r["warnings"])
    assert r["counts"] == {}


def test_load_parse_json_invalid(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("[1,2,3]", encoding="utf-8")
    with pytest.raises(ValueError, match="object"):
        load_parse_json(bad)


def test_cli_diff_subprocess(sample_fdx_path, tmp_path):
    repo = Path(__file__).resolve().parent.parent
    cli = repo / "cli.py"
    ja = tmp_path / "a.json"
    jb = tmp_path / "b.json"
    out = tmp_path / "diff.json"
    _run_parse_json(ja, sample_fdx_path, metadata=True, checksum=True)
    _run_parse_json(jb, sample_fdx_path, metadata=True, checksum=True)
    proc = subprocess.run(
        [
            sys.executable,
            str(cli),
            "diff",
            "--before",
            str(ja),
            "--after",
            str(jb),
            "-o",
            str(out),
        ],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=True,
    )
    assert proc.stdout == ""
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["diff_version"] == 1
    assert report["scenes"]["changed_indices"] == []


def test_scene_digests_ignore_removed_checksums(sample_fdx_path, tmp_path):
    """Recomputation is identical with or without ``checksums`` in the JSON."""
    out = tmp_path / "p.json"
    _run_parse_json(out, sample_fdx_path, metadata=False, checksum=True)
    data = json.loads(out.read_text(encoding="utf-8"))
    d1 = scene_digests(data)
    del data["checksums"]
    d2 = scene_digests(data)
    assert d1 == d2
