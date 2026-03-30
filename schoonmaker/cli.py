#!/usr/bin/env python3
from __future__ import annotations

import copy
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
from schoonmaker.parse_json_diff import (
    build_diff_report,
    diff_report_to_json,
    load_parse_json,
)
from schoonmaker.source_file_info import source_file_info
from schoonmaker.utils import get_logger, set_up_logging, strip_run_varying_ids
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


def _id_to_index_from_scenes(scenes: list) -> dict[str, int]:
    """Build scene id -> index from top-level scenes (metadata norm)."""
    if not isinstance(scenes, list):
        return {}
    return {
        s["id"]: i
        for i, s in enumerate(scenes)
        if isinstance(s, dict) and "id" in s
    }


def _normalize_metadata_for_checksum(
    metadata: dict, id_to_index: dict[str, int]
) -> dict:
    """Normalize metadata: scene_id/scene_ids -> indices for stable hash."""
    out = copy.deepcopy(metadata)
    if "scenes" in out and isinstance(out["scenes"], list):
        for i, item in enumerate(out["scenes"]):
            if isinstance(item, dict) and "scene_id" in item:
                sid = item.pop("scene_id")
                item["_index"] = id_to_index.get(sid, i)
    if "characters" in out and isinstance(out["characters"], dict):
        for char_data in out["characters"].values():
            if isinstance(char_data, dict) and "scene_ids" in char_data:
                ids = char_data["scene_ids"]
                char_data["scene_indices"] = sorted(
                    id_to_index.get(sid, -1) for sid in ids
                )
                del char_data["scene_ids"]
    return out


def _compute_output_checksums(out: dict) -> dict[str, object]:
    """SHA-256 hex digest of canonical JSON for key sections (for diffing)."""
    sections = ["alt_collection", "scenes", "title_page", "preamble"]
    if "metadata" in out:
        sections.append("metadata")
    id_to_index = _id_to_index_from_scenes(out.get("scenes"))
    result: dict[str, object] = {}
    for key in sections:
        val = out.get(key)
        if val is not None:
            if key == "metadata":
                normalized = _normalize_metadata_for_checksum(val, id_to_index)
            else:
                normalized = _normalize_for_checksum(key, val)
                normalized = strip_run_varying_ids(normalized)
            canonical = json.dumps(
                normalized, sort_keys=True, ensure_ascii=False
            )
            result[key] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if key == "scenes" and isinstance(normalized, list):
                result["scene_checksums"] = [
                    hashlib.sha256(
                        json.dumps(
                            scene,
                            sort_keys=True,
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).hexdigest()
                    for scene in normalized
                ]
    return result


def run_parse(args) -> int:
    screenplay = FDXParser(
        include_list_items=getattr(args, "list_items", False),
        include_display_boards=getattr(args, "display_boards", False),
    ).parse(args.file)
    out = {
        "nonce": uuid.uuid4().hex,
        "parser_version": parser_version,
        "parse_datetime": datetime.now(timezone.utc).isoformat(),
    }
    out.update(asdict(screenplay))
    if getattr(args, "metadata", False):
        out["metadata"] = compute_screenplay_metadata(screenplay)
    if getattr(args, "file_info", False):
        out["source_file"] = source_file_info(args.file)
    if getattr(args, "checksum", False):
        out["checksums"] = _compute_output_checksums(out)
    payload = json.dumps(out, indent=2, ensure_ascii=False)
    return _write_output(payload + "\n", getattr(args, "output", None))


def run_fountain(args) -> int:
    screenplay = FDXParser().parse(args.file)
    payload = screenplay_to_fountain(screenplay)
    return _write_output(payload, getattr(args, "output", None))


def run_diff(args) -> int:
    """Compare two parse JSON files; emit structured diff report JSON."""
    doc_a = load_parse_json(args.before)
    doc_b = load_parse_json(args.after)
    report = build_diff_report(
        doc_a,
        doc_b,
        label_a="before",
        label_b="after",
    )
    payload = diff_report_to_json(report)
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
    if args.command == "diff":
        return run_diff(args)
    if args.command == "ci-fdx-diff":
        from schoonmaker.ci_fdx_diff import main_ci_fdx_diff

        return main_ci_fdx_diff(args)
    if args.command == "ci-report-md":
        from schoonmaker.ci_report_md import main_ci_report_md

        return main_ci_report_md(args)

    log.error("Unknown command: %s", args.command)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
