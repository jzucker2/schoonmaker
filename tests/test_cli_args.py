"""Tests for CLI arg parsing: -f is per-subcommand and respected."""

import unittest

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
