"""Tests for CLI arg parsing: -f is per-subcommand and respected."""

import subprocess
import sys
import unittest
from pathlib import Path

from schoonmaker.cli_arg_parser import DEFAULT_SAMPLE_FILE_PATH, CLIArgParser


class TestCLIArgs(unittest.TestCase):
    def test_run_with_f_uses_given_file(self):
        args = CLIArgParser().parser.parse_args(["run", "-f", "custom.fdx"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.file, "custom.fdx")

    def test_run_without_f_uses_default(self):
        args = CLIArgParser().parser.parse_args(["run"])
        self.assertEqual(args.command, "run")
        self.assertEqual(args.file, DEFAULT_SAMPLE_FILE_PATH)

    def test_parse_with_f_uses_given_file(self):
        args = CLIArgParser().parser.parse_args(["parse", "-f", "other.fdx"])
        self.assertEqual(args.command, "parse")
        self.assertEqual(args.file, "other.fdx")

    def test_parse_file_info_flag(self):
        args = CLIArgParser().parser.parse_args(
            ["parse", "-f", "x.fdx", "--file-info"]
        )
        self.assertEqual(args.command, "parse")
        self.assertTrue(args.file_info)

    def test_parse_metadata_checksum_file_info_flags_together(self):
        args = CLIArgParser().parser.parse_args(
            [
                "parse",
                "-f",
                "script.fdx",
                "--metadata",
                "--checksum",
                "--file-info",
            ]
        )
        self.assertEqual(args.command, "parse")
        self.assertEqual(args.file, "script.fdx")
        self.assertTrue(args.metadata)
        self.assertTrue(args.checksum)
        self.assertTrue(args.file_info)

    def test_diff_before_after_short_flags(self):
        args = CLIArgParser().parser.parse_args(
            ["diff", "-b", "old.json", "-a", "new.json", "-o", "out.json"]
        )
        self.assertEqual(args.command, "diff")
        self.assertEqual(args.before, "old.json")
        self.assertEqual(args.after, "new.json")
        self.assertEqual(args.output, "out.json")


def test_python_m_schoonmaker_run_help():
    """``python -m schoonmaker`` works from the repo (package layout + __main__)."""  # noqa: E501
    repo_root = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, "-m", "schoonmaker", "run", "-h"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, (r.stdout, r.stderr)
