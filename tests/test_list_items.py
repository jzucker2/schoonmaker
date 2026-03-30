"""Optional <ListItems> parsing; beat board must not affect script metadata."""

from __future__ import annotations

import json
from types import SimpleNamespace

from schoonmaker.cli import run_parse
from schoonmaker.fdx import FDXParser
from schoonmaker.metadata import compute_screenplay_metadata


def test_list_items_empty_by_default(sample_fdx12_path):
    screenplay = FDXParser().parse(str(sample_fdx12_path))
    assert screenplay.list_items == []


def test_parse_includes_list_items_when_requested(sample_fdx12_path):
    screenplay = FDXParser(include_list_items=True).parse(
        str(sample_fdx12_path)
    )
    assert len(screenplay.list_items) >= 12
    beats = [
        x for x in screenplay.list_items if x["attrs"].get("Type") == "Beat"
    ]
    assert len(beats) >= 10
    with_notes = [b for b in beats if b.get("content_paragraphs")]
    assert len(with_notes) >= 1
    para = with_notes[0]["content_paragraphs"][0]
    assert para["raw_text"]


def test_list_items_peer_link_attrs_only(sample_fdx12_path):
    screenplay = FDXParser(include_list_items=True).parse(
        str(sample_fdx12_path)
    )
    links = [
        x
        for x in screenplay.list_items
        if x["attrs"].get("Type") == "PeerLink"
    ]
    assert len(links) >= 1
    assert "content_paragraphs" not in links[0]


def test_metadata_same_with_or_without_list_items(sample_fdx12_path):
    base = FDXParser(include_list_items=False).parse(str(sample_fdx12_path))
    with_li = FDXParser(include_list_items=True).parse(str(sample_fdx12_path))
    assert len(with_li.list_items) > 0
    ma = compute_screenplay_metadata(base)
    mb = compute_screenplay_metadata(with_li)
    # UUIDs differ per parse; ``characters`` / ``scenes`` embed scene ids.
    skip = {"characters", "scenes"}
    for key in ma:
        if key not in skip:
            assert ma[key] == mb[key], key


def test_parse_cli_list_items_flag_json(sample_fdx12_path, tmp_path):
    """``parse --list-items`` emits non-empty list_items in JSON."""
    out = tmp_path / "out.json"
    args = SimpleNamespace(
        command="parse",
        file=str(sample_fdx12_path),
        output=str(out),
        metadata=False,
        checksum=False,
        file_info=False,
        list_items=True,
        display_boards=False,
    )
    assert run_parse(args) == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data["list_items"]) >= 12
