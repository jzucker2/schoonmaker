"""Filesystem metadata for the FDX path (optional parse JSON field)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _ts_iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _best_effort_created_epoch(st: os.stat_result) -> float | None:
    """Creation time when the OS exposes it; else None."""
    birth = getattr(st, "st_birthtime", None)
    if birth is not None:
        return float(birth)
    if os.name == "nt":
        return float(st.st_ctime)
    return None


def source_file_info(path: str | os.PathLike[str]) -> dict[str, Any]:
    """
    Return JSON-friendly stats for a file path (path, size, timestamps).

    ``created`` is set on Windows (st_ctime) and macOS/BSD (st_birthtime);
    on typical Linux it is omitted (no portable creation time).
    """
    given = os.fspath(path)
    p = Path(given).expanduser()
    st = os.stat(p, follow_symlinks=True)
    resolved = p.resolve()
    created_epoch = _best_effort_created_epoch(st)
    out: dict[str, Any] = {
        "path_as_given": given,
        "path_resolved": str(resolved),
        "name": resolved.name,
        "size_bytes": st.st_size,
        "modified": _ts_iso_utc(st.st_mtime),
        "accessed": _ts_iso_utc(st.st_atime),
    }
    if created_epoch is not None:
        out["created"] = _ts_iso_utc(created_epoch)
    return out
