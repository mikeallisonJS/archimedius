"""Shared file-level metadata helpers."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("MediaOrganizer")


def best_creation_timestamp(stat_result) -> float:
    """Return the closest available creation timestamp for the current platform."""
    if sys.platform == "win32":
        return stat_result.st_ctime
    birthtime = getattr(stat_result, "st_birthtime", None)
    if birthtime is not None:
        return birthtime
    return stat_result.st_mtime


def add_common_file_metadata(metadata: dict, file_path: Path) -> None:
    """Add filename, extension, size, and creation date fields."""
    metadata["filename"] = file_path.stem
    metadata["filename_with_extension"] = file_path.name
    metadata["extension"] = file_path.suffix.lower()[1:]

    try:
        stat_result = file_path.stat()
    except OSError:
        return

    creation_time = datetime.fromtimestamp(best_creation_timestamp(stat_result))
    metadata["size"] = stat_result.st_size
    metadata["creation_date"] = creation_time.strftime("%Y-%m-%d")
    metadata["creation_year"] = creation_time.strftime("%Y")
    metadata["creation_month"] = creation_time.strftime("%m")
    metadata["creation_month_name"] = creation_time.strftime("%B")
