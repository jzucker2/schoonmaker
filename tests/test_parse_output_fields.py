"""Tests for parse output: nonce, parser_version, parse_datetime, checksums."""

import json
import re

from schoonmaker.version import version as PARSER_VERSION


def test_parse_output_has_nonce(sample_fdx_path, tmp_path):
    """Parse output includes nonce (unique per run)."""
    from cli import run_parse

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
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "nonce" in data
    assert isinstance(data["nonce"], str)
    assert len(data["nonce"]) == 32
    assert re.match(
        r"^[a-f0-9]+$", data["nonce"]
    ), "nonce must be 32 hex chars"


def test_parse_output_has_parser_version(sample_fdx_path, tmp_path):
    """Parse output includes parser_version from version.py."""
    from cli import run_parse

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
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "parser_version" in data
    assert data["parser_version"] == PARSER_VERSION


def test_parse_output_has_parse_datetime(sample_fdx_path, tmp_path):
    """Parse output includes parse_datetime (ISO format)."""
    from cli import run_parse

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
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "parse_datetime" in data
    dt = data["parse_datetime"]
    assert "T" in dt and "Z" in dt or "+" in dt, "expect ISO with timezone"


def test_parse_output_nonce_differs_each_run(sample_fdx_path, tmp_path):
    """Two parse runs produce different nonces."""
    from cli import run_parse

    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    def make_args(output_path):
        a = type(
            "Args",
            (),
            {
                "command": "parse",
                "file": str(sample_fdx_path),
                "metadata": False,
                "checksum": False,
            },
        )()
        a.output = str(output_path)
        return a

    run_parse(make_args(out1))
    run_parse(make_args(out2))
    d1 = json.loads(out1.read_text(encoding="utf-8"))
    d2 = json.loads(out2.read_text(encoding="utf-8"))
    assert d1["nonce"] != d2["nonce"]


def test_parse_with_checksum_includes_checksums(sample_fdx_path, tmp_path):
    """With --checksum, output has checksums for alts, scenes, etc."""
    from cli import run_parse

    out = tmp_path / "out.json"
    args = type(
        "Args",
        (),
        {
            "command": "parse",
            "file": str(sample_fdx_path),
            "output": str(out),
            "metadata": False,
            "checksum": True,
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "checksums" in data
    c = data["checksums"]
    assert "alt_collection" in c
    assert "scenes" in c
    assert "title_page" in c
    assert "preamble" in c
    for key, val in c.items():
        assert isinstance(val, str)
        assert len(val) == 64
        assert re.match(r"^[a-f0-9]+$", val), f"{key} checksum must be 64 hex"


def test_parse_with_metadata_and_checksum_includes_metadata_checksum(
    sample_fdx_path, tmp_path
):
    """With --metadata and --checksum, output has a metadata checksum."""
    from cli import run_parse

    out = tmp_path / "out.json"
    args = type(
        "Args",
        (),
        {
            "command": "parse",
            "file": str(sample_fdx_path),
            "output": str(out),
            "metadata": True,
            "checksum": True,
        },
    )()
    run_parse(args)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "checksums" in data
    assert "metadata" in data["checksums"]
    assert len(data["checksums"]["metadata"]) == 64
    assert re.match(
        r"^[a-f0-9]+$", data["checksums"]["metadata"]
    ), "metadata checksum must be 64 hex"


def test_parse_metadata_checksum_deterministic(sample_fdx_path, tmp_path):
    """Same file with --metadata and --checksum: metadata checksum is equal."""
    from cli import run_parse

    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    def make_args(output_path):
        return type(
            "Args",
            (),
            {
                "command": "parse",
                "file": str(sample_fdx_path),
                "output": str(output_path),
                "metadata": True,
                "checksum": True,
            },
        )()

    run_parse(make_args(out1))
    run_parse(make_args(out2))
    d1 = json.loads(out1.read_text(encoding="utf-8"))
    d2 = json.loads(out2.read_text(encoding="utf-8"))
    assert "checksums" in d1 and "metadata" in d1["checksums"]
    assert d1["checksums"]["metadata"] == d2["checksums"]["metadata"]


def test_parse_checksums_deterministic_with_dual_dialogue(
    sample_fdx13_path, tmp_path
):
    """With dual dialogue, scenes and preamble checksums are deterministic."""
    from cli import run_parse

    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    def make_args(output_path):
        return type(
            "Args",
            (),
            {
                "command": "parse",
                "file": str(sample_fdx13_path),
                "output": str(output_path),
                "metadata": False,
                "checksum": True,
            },
        )()

    run_parse(make_args(out1))
    run_parse(make_args(out2))
    d1 = json.loads(out1.read_text(encoding="utf-8"))
    d2 = json.loads(out2.read_text(encoding="utf-8"))
    assert d1["checksums"]["scenes"] == d2["checksums"]["scenes"]
    assert d1["checksums"]["preamble"] == d2["checksums"]["preamble"]


def test_parse_checksums_deterministic(sample_fdx_path, tmp_path):
    """Same file parsed twice with --checksum yields same checksums."""
    from cli import run_parse

    out1 = tmp_path / "out1.json"
    out2 = tmp_path / "out2.json"

    def make_args(output_path):
        a = type(
            "Args",
            (),
            {
                "command": "parse",
                "file": str(sample_fdx_path),
                "metadata": False,
                "checksum": True,
            },
        )()
        a.output = str(output_path)
        return a

    run_parse(make_args(out1))
    run_parse(make_args(out2))
    d1 = json.loads(out1.read_text(encoding="utf-8"))
    d2 = json.loads(out2.read_text(encoding="utf-8"))
    assert d1["checksums"] == d2["checksums"]
