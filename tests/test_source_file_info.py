"""Tests for optional source file filesystem metadata in parse JSON."""

import json
import time
from datetime import datetime, timezone

from schoonmaker.source_file_info import source_file_info


def test_source_file_info_matches_file(tmp_path):
    """source_file_info reports path, name, size, and ISO timestamps."""
    f = tmp_path / "script.fdx"
    f.write_text("<Content></Content>", encoding="utf-8")
    before = time.time()
    info = source_file_info(f)
    after = time.time()
    assert info["path_as_given"] == str(f)
    assert info["path_resolved"] == str(f.resolve())
    assert info["name"] == "script.fdx"
    assert info["size_bytes"] == len(f.read_bytes())
    for key in ("modified", "accessed"):
        assert "T" in info[key] and ("Z" in info[key] or "+" in info[key])
    mod = datetime.fromisoformat(info["modified"].replace("Z", "+00:00"))
    if mod.tzinfo is None:
        mod = mod.replace(tzinfo=timezone.utc)
    assert before - 5 <= mod.timestamp() <= after + 5


def test_parse_with_file_info_includes_source_file(sample_fdx_path, tmp_path):
    """With --file-info, JSON includes source_file with expected keys."""
    from schoonmaker.cli import run_parse

    out = tmp_path / "out.json"
    args = type(
        "Args",
        (),
        {
            "command": "parse",
            "file": str(sample_fdx_path),
            "output": str(out),
            "metadata": False,
            "checksum": False,
            "file_info": True,
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "source_file" in data
    sf = data["source_file"]
    assert sf["name"] == sample_fdx_path.name
    assert sf["size_bytes"] == sample_fdx_path.stat().st_size
    assert "path_resolved" in sf and "modified" in sf and "accessed" in sf
