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
    from cli import run_parse

    out = tmp_path / "out.json"
    args = ParseArgs(sample_fdx_path, out, metadata=False)
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" not in data


def test_metadata_with_flag_includes_metadata(sample_fdx_path, tmp_path):
    """With --metadata, JSON has 'metadata' key with expected structure."""
    from cli import run_parse

    out = tmp_path / "out.json"
    args = ParseArgs(sample_fdx_path, out, metadata=True)
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" in data
    meta = data["metadata"]
    assert "scenes_count" in meta
    assert "elements" in meta
    assert "characters" in meta
    assert "scenes" in meta
    assert "total_action_count" in meta
    assert "total_dialogue_block_count" in meta
    assert "total_dialogue_line_count" in meta
    assert "total_lines_count" in meta
    assert meta["scenes_count"] == len(data["scenes"])


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
        meta["total_lines_count"] == 4
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


def test_metadata_aggregates_match_per_scene_and_elements(sample_fdx_path):
    """Totals match sum of per-scene counts; total_lines matches elements."""
    screenplay = FDXParser().parse(str(sample_fdx_path))
    meta = compute_screenplay_metadata(screenplay)
    # total_* should match sum over scenes
    assert meta["total_action_count"] == sum(
        s["action_count"] for s in meta["scenes"]
    )
    assert meta["total_dialogue_block_count"] == sum(
        s["dialogue_block_count"] for s in meta["scenes"]
    )
    assert meta["total_dialogue_line_count"] == sum(
        s["dialogue_line_count"] for s in meta["scenes"]
    )
    # total_lines_count = sum of element-type counts (excl. dialogue_line)
    expected_total_lines = (
        meta["elements"]["action"]
        + meta["elements"]["dialogue_block"]
        + meta["elements"]["transition"]
        + meta["elements"]["shot"]
        + meta["elements"]["general"]
        + meta["elements"]["lyric"]
    )
    assert meta["total_lines_count"] == expected_total_lines
    # Each character's scenes_count should equal len(scene_ids)
    for name, data in meta["characters"].items():
        assert data["scenes_count"] == len(data["scene_ids"])
    # Per-scene character_line_count should sum to scene dialogue_line_count
    for scene in meta["scenes"]:
        assert scene["dialogue_line_count"] == sum(
            scene["character_line_count"].values()
        )


def test_metadata_cli_subprocess(sample_fdx_path, tmp_path):
    """python cli.py parse --metadata -f <fdx> -o <path> writes metadata."""
    import subprocess
    import sys

    out = tmp_path / "meta_out.json"
    repo_root = Path(__file__).resolve().parent.parent
    cli_py = repo_root / "cli.py"
    result = subprocess.run(
        [
            sys.executable,
            str(cli_py),
            "parse",
            "--metadata",
            "-f",
            str(sample_fdx_path),
            "-o",
            str(out),
        ],
        capture_output=True,
        text=True,
        cwd=str(cli_py.parent),
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "metadata" in data
    assert data["metadata"]["scenes_count"] == 2
    assert data["metadata"]["total_dialogue_line_count"] == 1
