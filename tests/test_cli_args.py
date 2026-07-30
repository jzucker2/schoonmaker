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

    def test_parse_list_items_flag(self):
        args = CLIArgParser().parser.parse_args(
            ["parse", "-f", "x.fdx", "--list-items"]
        )
        self.assertEqual(args.command, "parse")
        self.assertTrue(args.list_items)

    def test_parse_display_boards_flag(self):
        args = CLIArgParser().parser.parse_args(
            ["parse", "-f", "x.fdx", "--display-boards"]
        )
        self.assertEqual(args.command, "parse")
        self.assertTrue(args.display_boards)

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

    def test_ci_fdx_diff_output_and_shas(self):
        args = CLIArgParser().parser.parse_args(
            [
                "ci-fdx-diff",
                "-o",
                "reports",
                "--base-sha",
                "aaa",
                "--head-sha",
                "bbb",
            ]
        )
        self.assertEqual(args.command, "ci-fdx-diff")
        self.assertEqual(args.output, "reports")
        self.assertEqual(args.base_sha, "aaa")
        self.assertEqual(args.head_sha, "bbb")

    def test_ci_fdx_diff_list_items_and_display_boards_flags(self):
        args = CLIArgParser().parser.parse_args(
            [
                "ci-fdx-diff",
                "-o",
                "r",
                "--list-items",
                "--display-boards",
            ]
        )
        self.assertEqual(args.command, "ci-fdx-diff")
        self.assertTrue(args.list_items)
        self.assertTrue(args.display_boards)

    def test_next_semver_from_tags_flag(self):
        args = CLIArgParser().parser.parse_args(
            ["next-semver", "--from-tags", "--default", "v1.0.0"]
        )
        self.assertEqual(args.command, "next-semver")
        self.assertTrue(args.from_tags)
        self.assertEqual(args.default, "v1.0.0")

    def test_ci_release_notes_version_and_pr(self):
        args = CLIArgParser().parser.parse_args(
            [
                "ci-release-notes",
                "fdx-reports",
                "--version",
                "v1.2.4",
                "--pr",
                "9",
            ]
        )
        self.assertEqual(args.command, "ci-release-notes")
        self.assertEqual(args.reports_dir, "fdx-reports")
        self.assertEqual(args.version, "v1.2.4")
        self.assertEqual(args.pr_number, 9)

    def test_ci_select_pr_label(self):
        args = CLIArgParser().parser.parse_args(
            ["ci-select-pr", "--label", "release-ready"]
        )
        self.assertEqual(args.command, "ci-select-pr")
        self.assertEqual(args.label, "release-ready")


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
