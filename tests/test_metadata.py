"""Tests for screenplay metadata computation and CLI --metadata flag."""

import json
from pathlib import Path

from schoonmaker.fdx import FDXParser
from schoonmaker.metadata import compute_screenplay_metadata


class ParseArgs:
    def __init__(self, file_path, output_path, metadata=False):
        self.command = "parse"
        self.file = str(file_path)
        self.output = str(output_path)
        self.metadata = metadata


def test_metadata_without_flag_omits_metadata(sample_fdx_path, tmp_path):
    """parse without --metadata does not include 'metadata' key in JSON."""
    from schoonmaker.cli import run_parse

    out = tmp_path / "out.json"
    args = ParseArgs(sample_fdx_path, out, metadata=False)
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" not in data


def test_metadata_with_flag_includes_metadata(sample_fdx_path, tmp_path):
    """With --metadata, JSON has 'metadata' key with expected structure."""
    from schoonmaker.cli import run_parse

    out = tmp_path / "out.json"
    args = ParseArgs(sample_fdx_path, out, metadata=True)
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" in data
    meta = data["metadata"]
    assert "scenes_count" in meta
    assert "elements" in meta
    assert "characters" in meta
    assert "preamble" in meta
    assert "scenes" in meta
    assert "total_action_count" in meta
    assert "total_dialogue_block_count" in meta
    assert "total_dialogue_line_count" in meta
    assert "total_paragraphs_count" in meta
    assert "total_action_words" in meta
    assert "total_dialogue_words" in meta
    assert "total_scene_heading_count" in meta
    assert "total_scene_heading_words" in meta
    assert "total_locations_count" in meta
    assert "locations" in meta
    assert "indoor_locations_count" in meta
    assert "outdoor_locations_count" in meta
    assert "indoor_locations" in meta
    assert "outdoor_locations" in meta
    assert "indoor_scenes_count" in meta
    assert "outdoor_scenes_count" in meta
    assert "other_locations_count" in meta
    assert "other_locations" in meta
    assert "other_scenes_count" in meta
    assert "total_parenthetical_count" in meta
    assert "total_parenthetical_words" in meta
    assert "total_words" in meta
    assert "total_paragraphs_count" in meta
    assert meta["scenes_count"] == len(data["scenes"])
    assert "action_count" in meta["preamble"]
    assert "dialogue_block_count" in meta["preamble"]
    assert "dialogue_line_count" in meta["preamble"]


def test_metadata_compute_screenplay(sample_fdx_path):
    """compute_screenplay_metadata returns correct counts for sample.fdx."""
    screenplay = FDXParser().parse(str(sample_fdx_path))
    meta = compute_screenplay_metadata(screenplay)
    # sample.fdx: 2 scenes, 1 action, 1 dialogue, 1 transition, 1 general
    assert meta["scenes_count"] == 2
    assert meta["elements"]["action"] == 1
    assert meta["elements"]["dialogue_block"] == 1
    assert meta["elements"]["dialogue_line"] == 1
    assert meta["elements"]["transition"] == 1
    assert meta["elements"]["general"] == 1
    assert meta["elements"]["shot"] == 0
    assert meta["elements"]["lyric"] == 0
    assert meta["total_action_count"] == 1
    assert meta["total_dialogue_block_count"] == 1
    assert meta["total_dialogue_line_count"] == 1
    assert (
        meta["total_paragraphs_count"] == 4
    )  # action + dialogue_block + transition + general
    assert len(meta["scenes"]) == 2
    # Character JOHN (parser strips "(V.O.)" to modifiers)
    chars = meta["characters"]
    assert "JOHN" in chars
    assert chars["JOHN"]["scenes_count"] == 1
    assert chars["JOHN"]["dialogue_lines_count"] == 1
    assert len(chars["JOHN"]["scene_ids"]) == 1
    assert chars["JOHN"]["scene_ids"][0] == screenplay.scenes[0].id
    # Scene 0: 1 action, 1 dialogue block, 1 transition → lines_count 3
    scene0 = meta["scenes"][0]
    assert "JOHN" in scene0["characters"]
    assert scene0["character_line_count"]["JOHN"] == 1
    assert scene0["action_count"] == 1
    assert scene0["dialogue_block_count"] == 1
    assert scene0["dialogue_line_count"] == 1
    assert scene0["lines_count"] == 3
    # Scene 1: only general (empty line)
    scene1 = meta["scenes"][1]
    assert scene1["characters"] == []
    assert scene1["character_line_count"] == {}
    assert scene1["dialogue_block_count"] == 0
    assert scene1["dialogue_line_count"] == 0
    assert scene1["action_count"] == 0
    assert scene1["lines_count"] == 1
    # Scene headings: 2 headings, 8 words total (e.g. INT. APARTMENT - NIGHT)
    assert meta["total_scene_heading_count"] == 2
    assert meta["total_scene_heading_words"] == 8
    # Locations: 2 unique; INT. = indoor, EXT. = outdoor
    assert meta["total_locations_count"] == 2
    locs = {r["location"]: r["count"] for r in meta["locations"]}
    assert locs["INT. APARTMENT"] == 1
    assert locs["EXT. STREET"] == 1
    assert meta["indoor_locations_count"] == 1
    assert meta["outdoor_locations_count"] == 1
    assert meta["indoor_scenes_count"] == 1
    assert meta["outdoor_scenes_count"] == 1
    assert len(meta["indoor_locations"]) == 1
    assert meta["indoor_locations"][0]["location"] == "INT. APARTMENT"
    assert len(meta["outdoor_locations"]) == 1
    assert meta["outdoor_locations"][0]["location"] == "EXT. STREET"
    # Parenthetical: one "(whispering)" = 1 count, 1 word
    assert meta["total_parenthetical_count"] == 1
    assert meta["total_parenthetical_words"] == 1
    # Word counts: action 4, dialogue 1, parenthetical 1, scene heading 8,
    # transition 2, general 0 → total 16
    assert meta["total_action_words"] == 4
    assert meta["total_dialogue_words"] == 1
    assert meta["total_words"] == 16


def test_metadata_word_counts_accuracy(sample_fdx_path):
    """Word counts: dialogue, action, parenthetical, scene heading, total."""
    screenplay = FDXParser().parse(str(sample_fdx_path))
    meta = compute_screenplay_metadata(screenplay)
    assert meta["total_action_words"] == 4
    assert meta["total_dialogue_words"] == 1
    assert meta["total_parenthetical_words"] == 1
    assert meta["total_scene_heading_words"] == 8
    assert meta["total_words"] == 16
    assert (
        meta["total_words"]
        >= meta["total_action_words"]
        + meta["total_dialogue_words"]
        + meta["total_parenthetical_words"]
        + meta["total_scene_heading_words"]
    )


def test_metadata_preamble_included_in_totals():
    """Totals include preamble; preamble + scenes sum to totals."""
    path = Path(__file__).parent / "fixtures" / "sample_with_preamble.fdx"
    assert path.exists()
    screenplay = FDXParser().parse(str(path))
    meta = compute_screenplay_metadata(screenplay)
    assert meta["preamble"]["action_count"] == 1
    assert len(meta["scenes"]) == 1
    assert meta["scenes"][0]["action_count"] == 1
    assert meta["total_action_count"] == 2
    assert (
        meta["preamble"]["action_count"]
        + sum(s["action_count"] for s in meta["scenes"])
        == meta["total_action_count"]
    )


def test_metadata_aggregates_match_per_scene_and_elements(sample_fdx_path):
    """Totals match preamble + sum of per-scene; total_paragraphs matches."""
    screenplay = FDXParser().parse(str(sample_fdx_path))
    meta = compute_screenplay_metadata(screenplay)
    pre = meta["preamble"]
    # total_* = preamble + sum over scenes
    assert meta["total_action_count"] == pre["action_count"] + sum(
        s["action_count"] for s in meta["scenes"]
    )
    block_total = pre["dialogue_block_count"] + sum(
        s["dialogue_block_count"] for s in meta["scenes"]
    )
    assert meta["total_dialogue_block_count"] == block_total
    line_total = pre["dialogue_line_count"] + sum(
        s["dialogue_line_count"] for s in meta["scenes"]
    )
    assert meta["total_dialogue_line_count"] == line_total
    # total_paragraphs_count = sum of element-type counts (paragraph elements)
    expected_paragraphs = (
        meta["elements"]["action"]
        + meta["elements"]["dialogue_block"]
        + meta["elements"]["transition"]
        + meta["elements"]["shot"]
        + meta["elements"]["general"]
        + meta["elements"]["lyric"]
    )
    assert meta["total_paragraphs_count"] == expected_paragraphs
    # Location counts sum to scene count (each heading counts once)
    assert sum(c["count"] for c in meta["locations"]) == meta["scenes_count"]
    # Indoor + outdoor + other scenes = total scenes
    assert (
        meta["indoor_scenes_count"]
        + meta["outdoor_scenes_count"]
        + meta["other_scenes_count"]
        == meta["scenes_count"]
    )
    # Each character's scenes_count should equal len(scene_ids)
    for name, data in meta["characters"].items():
        assert data["scenes_count"] == len(data["scene_ids"])
    # Per-scene character_line_count should sum to scene dialogue_line_count
    for scene in meta["scenes"]:
        assert scene["dialogue_line_count"] == sum(
            scene["character_line_count"].values()
        )


def test_metadata_cli_subprocess(sample_fdx_path, tmp_path):
    """``python -m schoonmaker parse --metadata`` writes metadata."""
    import subprocess
    import sys

    out = tmp_path / "meta_out.json"
    repo_root = Path(__file__).resolve().parent.parent
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "schoonmaker",
            "parse",
            "--metadata",
            "-f",
            str(sample_fdx_path),
            "-o",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert data["metadata"]["scenes_count"] == 2
    assert data["metadata"]["total_dialogue_line_count"] == 1
