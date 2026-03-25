"""Compare two schoonmaker parse JSON docs (e.g. same script, two saves)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from schoonmaker.utils import strip_run_varying_ids


DIFF_REPORT_VERSION = 1


def load_parse_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON file produced by ``cli.py parse``."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"parse JSON must be an object: {p}")
    return data


def _normalized_scene_for_digest(scene: dict, index: int) -> dict:
    """One scene dict normalized like parse scene checksum (no scene id)."""
    scene_copy = dict(scene)
    scene_copy.pop("id", None)
    scene_copy["_index"] = index
    return strip_run_varying_ids(scene_copy)


def scene_content_digest(scene: dict, index: int) -> str:
    """SHA-256 hex for one scene (same rules as parse ``scene_checksums``)."""
    normalized = _normalized_scene_for_digest(scene, index)
    canonical = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def scene_digests(data: dict[str, Any]) -> list[str]:
    """
    Per-scene content digests (always recomputed from ``scenes``).

    Ignores ``checksums.scene_checksums`` so edited JSON cannot carry stale
    per-scene hashes. Matches parse checksums when the document is unchanged.
    """
    scenes = data.get("scenes")
    if not isinstance(scenes, list):
        return []
    digests: list[str] = []
    for i, s in enumerate(scenes):
        if isinstance(s, dict):
            digests.append(scene_content_digest(s, i))
        else:
            digests.append(
                hashlib.sha256(
                    json.dumps({"_bad_scene": i}, sort_keys=True).encode(
                        "utf-8"
                    )
                ).hexdigest()
            )
    return digests


def _meta_counts(meta: dict[str, Any] | None) -> dict[str, int]:
    """
    Flat totals from ``compute_screenplay_metadata`` output (0 if missing).

    Word keys match metadata: action, dialogue, scene headings, and
    parentheticals only (transition/shot/general/lyric words roll into
    ``total_words`` but are not exposed separately there).
    """
    if not meta:
        return {}
    out: dict[str, int] = {}
    for key in (
        "total_words",
        "total_action_words",
        "total_dialogue_words",
        "total_scene_heading_words",
        "total_parenthetical_words",
        "total_parenthetical_count",
        "total_dialogue_line_count",
        "total_action_count",
        "total_dialogue_block_count",
        "total_paragraphs_count",
        "scenes_count",
        "indoor_scenes_count",
        "outdoor_scenes_count",
        "other_scenes_count",
        "total_locations_count",
        "indoor_locations_count",
        "outdoor_locations_count",
        "other_locations_count",
    ):
        v = meta.get(key)
        if isinstance(v, bool):
            out[key] = int(v)
        elif isinstance(v, int):
            out[key] = v
        else:
            out[key] = 0
    elements = meta.get("elements")
    if isinstance(elements, dict):
        for ek, ev in elements.items():
            if isinstance(ev, bool):
                out[f"elements.{ek}"] = int(ev)
            elif isinstance(ev, int):
                out[f"elements.{ek}"] = ev
            else:
                out[f"elements.{ek}"] = 0
    return out


def _location_list_to_map(rows: object) -> dict[str, int]:
    if not isinstance(rows, list):
        return {}
    out: dict[str, int] = {}
    for row in rows:
        if isinstance(row, dict) and "location" in row:
            loc = str(row["location"])
            cnt = row.get("count", 0)
            out[loc] = int(cnt) if isinstance(cnt, (int, float)) else 0
    return out


def _summarize_input(label: str, data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"label": label}
    out["parser_version"] = data.get("parser_version")
    out["parse_datetime"] = data.get("parse_datetime")
    out["nonce"] = data.get("nonce")
    sf = data.get("source_file")
    if isinstance(sf, dict):
        out["source_file"] = {
            "path_resolved": sf.get("path_resolved"),
            "path_as_given": sf.get("path_as_given"),
            "name": sf.get("name"),
            "modified": sf.get("modified"),
        }
    return out


def build_diff_report(
    a: dict[str, Any],
    b: dict[str, Any],
    *,
    label_a: str = "a",
    label_b: str = "b",
) -> dict[str, Any]:
    """
    Build a structured diff report (JSON-serializable).

    ``a`` is treated as the earlier / baseline document; ``b`` as the newer.
    Prefer parse output with ``--metadata`` for full word, character, and
    location stats. ``--checksum`` avoids recomputing per-scene digests when
    lists match scene count.
    """
    warnings: list[str] = []
    scenes_a = a.get("scenes")
    scenes_b = b.get("scenes")
    if not isinstance(scenes_a, list):
        raise ValueError(f"{label_a}: missing or invalid 'scenes' array")
    if not isinstance(scenes_b, list):
        raise ValueError(f"{label_b}: missing or invalid 'scenes' array")

    meta_a = a.get("metadata")
    meta_b = b.get("metadata")
    if not isinstance(meta_a, dict):
        warnings.append(
            f"{label_a} has no metadata; word/character/location stats "
            "are limited or omitted"
        )
        meta_a = None
    if not isinstance(meta_b, dict):
        warnings.append(
            f"{label_b} has no metadata; word/character/location stats "
            "are limited or omitted"
        )
        meta_b = None
    if (meta_a is None) != (meta_b is None):
        warnings.append(
            "Only one input has metadata; full word/character/location "
            "comparison needs --metadata on both parse runs"
        )

    dig_a = scene_digests(a)
    dig_b = scene_digests(b)
    n_a, n_b = len(scenes_a), len(scenes_b)
    n_min = min(n_a, n_b)
    changed_indices: list[int] = []
    for i in range(n_min):
        if i < len(dig_a) and i < len(dig_b) and dig_a[i] != dig_b[i]:
            changed_indices.append(i)
    added_scene_indices = list(range(n_a, n_b))
    removed_scene_indices = list(range(n_b, n_a))

    report: dict[str, Any] = {
        "diff_version": DIFF_REPORT_VERSION,
        "input": {
            label_a: _summarize_input(label_a, a),
            label_b: _summarize_input(label_b, b),
        },
        "scenes": {
            "count_before": n_a,
            "count_after": n_b,
            "added_count": max(0, n_b - n_a),
            "removed_count": max(0, n_a - n_b),
            "added_scene_indices": added_scene_indices,
            "removed_scene_indices": removed_scene_indices,
            "changed_indices": changed_indices,
            "unchanged_shared_count": n_min - len(changed_indices),
        },
        "warnings": warnings,
    }

    ca = _meta_counts(meta_a)
    cb = _meta_counts(meta_b)
    if meta_a is not None and meta_b is not None:
        all_keys = sorted(set(ca) | set(cb))
        words_detail: dict[str, Any] = {}
        for key in all_keys:
            va, vb = ca.get(key, 0), cb.get(key, 0)
            if va or vb or key in ("total_words",):
                words_detail[key] = {
                    "before": va,
                    "after": vb,
                    "delta": vb - va,
                }
        report["counts"] = words_detail

        # Element-type line-style summary (dialogue_line vs action etc.)
        el_keys = [k for k in all_keys if k.startswith("elements.")]
        report["elements"] = {
            k: {
                "before": ca.get(k, 0),
                "after": cb.get(k, 0),
                "delta": cb.get(k, 0) - ca.get(k, 0),
            }
            for k in sorted(el_keys)
        }

        chars_a = meta_a.get("characters") or {}
        chars_b = meta_b.get("characters") or {}
        if isinstance(chars_a, dict) and isinstance(chars_b, dict):
            names_a = set(chars_a.keys())
            names_b = set(chars_b.keys())
            new_names = sorted(names_b - names_a)
            gone_names = sorted(names_a - names_b)
            both = sorted(names_a & names_b)
            new_chars = []
            for name in new_names:
                row = chars_b.get(name)
                if isinstance(row, dict):
                    new_chars.append(
                        {
                            "name": name,
                            "dialogue_lines": row.get(
                                "dialogue_lines_count", 0
                            ),
                            "scenes_count": row.get("scenes_count", 0),
                        }
                    )
            removed_chars = []
            for name in gone_names:
                row = chars_a.get(name)
                if isinstance(row, dict):
                    removed_chars.append(
                        {
                            "name": name,
                            "dialogue_lines": row.get(
                                "dialogue_lines_count", 0
                            ),
                            "scenes_count": row.get("scenes_count", 0),
                        }
                    )
            line_changes = []
            for name in both:
                ra = chars_a.get(name) or {}
                rb = chars_b.get(name) or {}
                la = (
                    ra.get("dialogue_lines_count", 0)
                    if isinstance(ra, dict)
                    else 0
                )
                lb = (
                    rb.get("dialogue_lines_count", 0)
                    if isinstance(rb, dict)
                    else 0
                )
                sa = ra.get("scenes_count", 0) if isinstance(ra, dict) else 0
                sb = rb.get("scenes_count", 0) if isinstance(rb, dict) else 0
                if la != lb or sa != sb:
                    line_changes.append(
                        {
                            "name": name,
                            "dialogue_lines_before": la,
                            "dialogue_lines_after": lb,
                            "dialogue_lines_delta": lb - la,
                            "scenes_count_before": sa,
                            "scenes_count_after": sb,
                            "scenes_count_delta": sb - sa,
                        }
                    )
            report["characters"] = {
                "new": new_chars,
                "removed": removed_chars,
                "changed": line_changes,
            }

        def loc_diff(
            key: str,
        ) -> dict[str, Any]:
            ma = _location_list_to_map(meta_a.get(key))
            mb = _location_list_to_map(meta_b.get(key))
            keys = sorted(set(ma) | set(mb))
            rows = []
            for loc in keys:
                va, vb = ma.get(loc, 0), mb.get(loc, 0)
                if va != vb:
                    rows.append(
                        {
                            "location": loc,
                            "scene_count_before": va,
                            "scene_count_after": vb,
                            "delta": vb - va,
                        }
                    )
            return {"key": key, "changed": rows}

        report["locations"] = {
            "summary": {
                "total_locations_count": {
                    "before": meta_a.get("total_locations_count", 0),
                    "after": meta_b.get("total_locations_count", 0),
                    "delta": meta_b.get("total_locations_count", 0)
                    - meta_a.get("total_locations_count", 0),
                },
                "indoor_scenes_count": {
                    "before": meta_a.get("indoor_scenes_count", 0),
                    "after": meta_b.get("indoor_scenes_count", 0),
                    "delta": meta_b.get("indoor_scenes_count", 0)
                    - meta_a.get("indoor_scenes_count", 0),
                },
                "outdoor_scenes_count": {
                    "before": meta_a.get("outdoor_scenes_count", 0),
                    "after": meta_b.get("outdoor_scenes_count", 0),
                    "delta": meta_b.get("outdoor_scenes_count", 0)
                    - meta_a.get("outdoor_scenes_count", 0),
                },
                "other_scenes_count": {
                    "before": meta_a.get("other_scenes_count", 0),
                    "after": meta_b.get("other_scenes_count", 0),
                    "delta": meta_b.get("other_scenes_count", 0)
                    - meta_a.get("other_scenes_count", 0),
                },
            },
            "by_bucket": [
                loc_diff("locations"),
                loc_diff("indoor_locations"),
                loc_diff("outdoor_locations"),
                loc_diff("other_locations"),
            ],
        }
    else:
        report["counts"] = {}
        report["elements"] = {}
        report["characters"] = {
            "new": [],
            "removed": [],
            "changed": [],
        }
        report["locations"] = {
            "summary": {},
            "by_bucket": [],
        }

    return report


def diff_report_to_json(report: dict[str, Any], *, indent: int = 2) -> str:
    return json.dumps(report, indent=indent, ensure_ascii=False) + "\n"
