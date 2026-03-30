"""Optional <DisplayBoards> parsing; excluded from script metadata totals."""

from __future__ import annotations

import json
from types import SimpleNamespace

from schoonmaker.cli import run_parse
from schoonmaker.fdx import FDXParser
from schoonmaker.metadata import compute_screenplay_metadata


def test_display_boards_empty_by_default(sample_fdx12_path):
    screenplay = FDXParser().parse(str(sample_fdx12_path))
    assert screenplay.display_boards == []


def test_parse_includes_display_boards_when_requested(sample_fdx12_path):
    screenplay = FDXParser(include_display_boards=True).parse(
        str(sample_fdx12_path)
    )
    assert len(screenplay.display_boards) == 2
    types = {b["attrs"].get("Type") for b in screenplay.display_boards}
    assert types == {"StoryMap", "Beat"}
    story = next(
        b
        for b in screenplay.display_boards
        if b["attrs"]["Type"] == "StoryMap"
    )
    beat = next(
        b for b in screenplay.display_boards if b["attrs"]["Type"] == "Beat"
    )
    assert len(story["items"]) >= 14
    assert len(beat["items"]) >= 15
    assert all("Id" in it for it in story["items"])
    placed = [it for it in beat["items"] if "Left" in it]
    assert len(placed) >= 10


def test_metadata_unchanged_by_display_boards(sample_fdx12_path):
    base = FDXParser(include_display_boards=False).parse(
        str(sample_fdx12_path)
    )
    with_db = FDXParser(include_display_boards=True).parse(
        str(sample_fdx12_path)
    )
    assert len(with_db.display_boards) == 2
    ma = compute_screenplay_metadata(base)
    mb = compute_screenplay_metadata(with_db)
    skip = {"characters", "scenes"}
    for key in ma:
        if key not in skip:
            assert ma[key] == mb[key], key


def test_parse_cli_display_boards_flag(sample_fdx12_path, tmp_path):
    out = tmp_path / "out.json"
    args = SimpleNamespace(
        command="parse",
        file=str(sample_fdx12_path),
        output=str(out),
        metadata=False,
        checksum=False,
        file_info=False,
        list_items=False,
        display_boards=True,
    )
    assert run_parse(args) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["display_boards"]) == 2
