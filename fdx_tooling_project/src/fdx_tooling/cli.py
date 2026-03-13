from __future__ import annotations

from dataclasses import asdict
import argparse
import json
from pathlib import Path
import sys

from .fountain import screenplay_to_fountain
from .parser import FDXParser


def main() -> int:
    parser = argparse.ArgumentParser(prog="fdx-tool", description="Parse Final Draft FDX files")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="Convert FDX to JSON AST")
    parse_cmd.add_argument("input", help="Path to .fdx file")
    parse_cmd.add_argument("-o", "--output", help="Path to output JSON file")

    fountain_cmd = subparsers.add_parser("fountain", help="Convert FDX to Fountain")
    fountain_cmd.add_argument("input", help="Path to .fdx file")
    fountain_cmd.add_argument("-o", "--output", help="Path to output Fountain file")

    args = parser.parse_args()
    screenplay = FDXParser().parse(args.input)

    if args.command == "parse":
        payload = json.dumps(asdict(screenplay), indent=2, ensure_ascii=False)
        return _write_output(payload + "\n", args.output)

    if args.command == "fountain":
        payload = screenplay_to_fountain(screenplay)
        return _write_output(payload, args.output)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _write_output(text: str, output: str | None) -> int:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
