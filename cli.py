#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from dataclasses import asdict

from schoonmaker.cli_arg_parser import CLIArgParser
from schoonmaker.fdx import FDXParser, screenplay_to_fountain
from schoonmaker.metadata import compute_screenplay_metadata
from schoonmaker.utils import set_up_logging, get_logger
from schoonmaker.version import version as parser_version

set_up_logging()
log = get_logger(__name__)


def _write_output(text: str, output: str | None) -> int:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


def run_summary(args) -> int:
    """Parse FDX with FDXParser and print a short summary."""
    screenplay = FDXParser().parse(args.file)
    n_scenes = len(screenplay.scenes)
    log.info(
        "document_type=%s version=%s scenes=%d",
        screenplay.document_type,
        screenplay.version,
        n_scenes,
    )
    return 0


def _normalize_for_checksum(key: str, val: object) -> object:
    """Strip run-varying ids so checksums are deterministic."""
    if key != "scenes" or not isinstance(val, list):
        return val
    out_list = []
    for i, scene in enumerate(val):
        if not isinstance(scene, dict):
            out_list.append(scene)
            continue
        scene_copy = dict(scene)
        scene_copy.pop("id", None)
        scene_copy["_index"] = i
        out_list.append(scene_copy)
    return out_list


def _compute_output_checksums(out: dict) -> dict[str, str]:
    """SHA-256 hex digest of canonical JSON for key sections (for diffing)."""
    sections = ["alt_collection", "scenes", "title_page", "preamble"]
    if "metadata" in out:
        sections.append("metadata")
    result = {}
    for key in sections:
        val = out.get(key)
        if val is not None:
            normalized = _normalize_for_checksum(key, val)
            canonical = json.dumps(
                normalized, sort_keys=True, ensure_ascii=False
            )
            result[key] = hashlib.sha256(
                canonical.encode("utf-8")
            ).hexdigest()
    return result


def run_parse(args) -> int:
    screenplay = FDXParser().parse(args.file)
    out = {
        "nonce": uuid.uuid4().hex,
        "parser_version": parser_version,
        "parse_datetime": datetime.now(timezone.utc).isoformat(),
    }
    out.update(asdict(screenplay))
    if getattr(args, "metadata", False):
        out["metadata"] = compute_screenplay_metadata(screenplay)
    if getattr(args, "checksum", False):
        out["checksums"] = _compute_output_checksums(out)
    payload = json.dumps(out, indent=2, ensure_ascii=False)
    return _write_output(payload + "\n", getattr(args, "output", None))


def run_fountain(args) -> int:
    screenplay = FDXParser().parse(args.file)
    payload = screenplay_to_fountain(screenplay)
    return _write_output(payload, getattr(args, "output", None))


def main() -> int:
    args = CLIArgParser.get_cli_args()
    log.info("cli_args: %s", args)

    if args.command == "run":
        return run_summary(args)
    if args.command == "parse":
        return run_parse(args)
    if args.command == "fountain":
        return run_fountain(args)

    log.error("Unknown command: %s", args.command)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
