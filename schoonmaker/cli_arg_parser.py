from __future__ import annotations

from argparse import ArgumentParser, Namespace

DEFAULT_SAMPLE_FILE_PATH = "samples/final_draft_12_sample.fdx"


class CLIArgParser(object):
    def __init__(self):
        self.parser = ArgumentParser(
            prog="schoonmaker",
            description=(
                "Parse FDX; export JSON AST or Fountain; diff parse JSON "
                "or CI reports; Markdown for GitHub Actions Step Summary."
            ),
        )
        subparsers = self.parser.add_subparsers(dest="command", required=True)

        run_parser = subparsers.add_parser(
            "run", help="Parse FDX and print a short summary"
        )
        run_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to input FDX file",
        )
        run_parser.set_defaults(command="run")

        parse_parser = subparsers.add_parser(
            "parse", help="Convert FDX to JSON AST"
        )
        parse_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to .fdx file",
        )
        parse_parser.add_argument(
            "-o", "--output", type=str, help="Path to output JSON file"
        )
        parse_parser.add_argument(
            "--metadata",
            action="store_true",
            help="Add computed metadata (scene/character/line counts) to JSON",
        )
        parse_parser.add_argument(
            "--checksum",
            action="store_true",
            help="Add SHA-256 checksums for sections to JSON output",
        )
        parse_parser.add_argument(
            "--file-info",
            action="store_true",
            dest="file_info",
            help="Include source file path, size, and timestamps in JSON",
        )
        parse_parser.add_argument(
            "--list-items",
            action="store_true",
            dest="list_items",
            help=(
                "Include Final Draft <ListItems> (beat/outline board) in "
                "JSON; excluded from --metadata script totals"
            ),
        )
        parse_parser.add_argument(
            "--display-boards",
            action="store_true",
            dest="display_boards",
            help=(
                "Include Final Draft <DisplayBoards> (Story Map / Beat "
                "layout) in JSON; excluded from --metadata script totals"
            ),
        )
        parse_parser.set_defaults(command="parse")

        fountain_parser = subparsers.add_parser(
            "fountain", help="Convert FDX to Fountain"
        )
        fountain_parser.add_argument(
            "-f",
            "--file",
            type=str,
            default=DEFAULT_SAMPLE_FILE_PATH,
            help="Path to .fdx file",
        )
        fountain_parser.add_argument(
            "-o", "--output", type=str, help="Path to output Fountain file"
        )
        fountain_parser.set_defaults(command="fountain")

        diff_parser = subparsers.add_parser(
            "diff",
            help="Compare two parse JSON files (before/after)",
        )
        diff_parser.add_argument(
            "--before",
            "-b",
            type=str,
            required=True,
            metavar="PATH",
            help="Earlier parse JSON baseline (-b for --before)",
        )
        diff_parser.add_argument(
            "--after",
            "-a",
            type=str,
            required=True,
            metavar="PATH",
            help="Later parse JSON (-a for --after)",
        )
        diff_parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Write diff report JSON to this path (default: stdout)",
        )
        diff_parser.set_defaults(command="diff")

        ci_parser = subparsers.add_parser(
            "ci-fdx-diff",
            help="Diff changed .fdx files between two git commits (CI)",
        )
        ci_parser.add_argument(
            "-o",
            "--output",
            type=str,
            required=True,
            help="Output directory for reports",
        )
        ci_parser.add_argument(
            "--base-sha",
            type=str,
            default="",
            dest="base_sha",
            help="Base commit (or CI_FDX_BASE_SHA)",
        )
        ci_parser.add_argument(
            "--head-sha",
            type=str,
            default="",
            dest="head_sha",
            help="Head commit (or CI_FDX_HEAD_SHA)",
        )
        ci_parser.add_argument(
            "--repo",
            type=str,
            default="",
            help="Git repository root (default: current directory)",
        )
        ci_parser.add_argument(
            "--list-items",
            action="store_true",
            dest="list_items",
            help=(
                "Parse with --list-items (or set CI_FDX_LIST_ITEMS=1); "
                "diff reports include list_items when non-empty"
            ),
        )
        ci_parser.add_argument(
            "--display-boards",
            action="store_true",
            dest="display_boards",
            help=(
                "Parse with --display-boards (or CI_FDX_DISPLAY_BOARDS=1); "
                "diff includes display_boards when non-empty"
            ),
        )
        ci_parser.set_defaults(command="ci-fdx-diff")

        report_md_parser = subparsers.add_parser(
            "ci-report-md",
            help=(
                "Emit Markdown from ci-fdx-diff *-diff.json (GitHub Summary)"
            ),
        )
        report_md_parser.add_argument(
            "reports_dir",
            nargs="?",
            default=".",
            help="Directory with *-diff.json and optional path-index.tsv",
        )
        report_md_parser.add_argument(
            "-o",
            "--output",
            type=str,
            help="Write Markdown here (default: stdout)",
        )
        report_md_parser.set_defaults(command="ci-report-md")

    def _parse_args(self) -> Namespace:
        return self.parser.parse_args()

    def get_args(self) -> Namespace:
        return self._parse_args()

    @classmethod
    def get_cli_args(cls) -> Namespace:
        parser = cls()
        return parser.get_args()
