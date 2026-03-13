from __future__ import annotations

from argparse import ArgumentParser, Namespace

DEFAULT_SAMPLE_FILE_PATH = "samples/final_draft_12_sample.fdx"


class CLIArgParser(object):
    def __init__(self):
        self.parser = ArgumentParser(
            prog="schoonmaker",
            description="Parse FDX files; export JSON AST or Fountain.",
        )
        self.parser.add_argument(
            "-f",
            "--file",
            type=str,
            help="Path to input FDX file",
            default=DEFAULT_SAMPLE_FILE_PATH,
        )
        subparsers = self.parser.add_subparsers(dest="command", required=True)

        run_parser = subparsers.add_parser(
            "run", help="Parse FDX and print a short summary"
        )
        run_parser.add_argument(
            "-f", "--file", type=str, default=DEFAULT_SAMPLE_FILE_PATH
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

    def _parse_args(self) -> Namespace:
        return self.parser.parse_args()

    def get_args(self) -> Namespace:
        return self._parse_args()

    @classmethod
    def get_cli_args(cls) -> Namespace:
        parser = cls()
        return parser.get_args()
