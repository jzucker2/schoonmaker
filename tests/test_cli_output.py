"""Tests that parse/fountain with -o create the output file."""

import json
import subprocess
import sys
from pathlib import Path


def test_parse_o_creates_output_file(sample_fdx_path, tmp_path):
    """parse -f <fdx> -o <path> creates the file and writes valid JSON."""
    out = tmp_path / "out.json"
    from cli import run_parse

    class Args:
        command = "parse"
        file = str(sample_fdx_path)
        output = str(out)

    args = Args()
    run_parse(args)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["document_type"] == "Script"
    assert "scenes" in data
    assert len(data["scenes"]) >= 1


def test_fountain_o_creates_output_file(sample_fdx_path, tmp_path):
    """fountain -f <fdx> -o <path> creates the file with Fountain text."""
    out = tmp_path / "out.fountain"
    from cli import run_fountain

    class Args:
        command = "fountain"
        file = str(sample_fdx_path)
        output = str(out)

    args = Args()
    run_fountain(args)
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "INT. APARTMENT - NIGHT" in text
    assert "JOHN" in text


def test_parse_via_subprocess_creates_file(sample_fdx_path, tmp_path):
    """'python cli.py parse -f <fdx> -o <path>' creates the output file."""
    out = tmp_path / "subprocess_out.json"
    repo_root = Path(__file__).resolve().parent.parent
    cli_py = repo_root / "cli.py"
    cmd = [
        sys.executable,
        str(cli_py),
        "parse",
        "-f",
        str(sample_fdx_path),
        "-o",
        str(out),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cli_py.parent),
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    assert out.exists()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["document_type"] == "Script"
