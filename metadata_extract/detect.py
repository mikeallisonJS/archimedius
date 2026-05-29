"""Media type detection from file extension."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence


def detect_media_type(
    file_path: str | Path,
    supported_extensions: Mapping[str, Sequence[str]],
) -> str:
    """Determine the media type for a file from its extension."""
    ext = Path(file_path).suffix.lower()
    for media_type, extensions_list in supported_extensions.items():
        if ext in extensions_list:
            return media_type
    return "unknown"
