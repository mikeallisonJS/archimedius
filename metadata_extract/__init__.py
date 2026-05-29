"""
Metadata extraction for Archimedius media files.

Extracts embedded tags and file properties without resolving destination paths.
Per-media-type implementations are registered in ``registry.MEDIA_TYPE_EXTRACTORS``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping, Sequence

from metadata_extract.common import add_common_file_metadata, best_creation_timestamp
from metadata_extract.detect import detect_media_type
from metadata_extract.registry import MEDIA_TYPE_EXTRACTORS

logger = logging.getLogger("MediaOrganizer")

# Backward-compatible alias for tests that patch platform behavior.
_best_creation_timestamp = best_creation_timestamp


def extract_metadata(
    file_path: str | Path,
    media_type: str | None = None,
    supported_extensions: Mapping[str, Sequence[str]] | None = None,
) -> dict:
    """
    Extract metadata for a media file without resolving destination paths.

    Args:
        file_path: Path to the media file.
        media_type: Optional pre-detected media type.
        supported_extensions: Required when media_type is not provided.

    Returns:
        Dictionary of metadata fields for the file.
    """
    path = Path(file_path)
    if media_type is None:
        if supported_extensions is None:
            raise ValueError("supported_extensions is required when media_type is omitted")
        media_type = detect_media_type(path, supported_extensions)

    metadata: dict = {}

    try:
        extractor = MEDIA_TYPE_EXTRACTORS.get(media_type)
        if extractor is not None:
            extractor(path, metadata)

        add_common_file_metadata(metadata, path)
    except Exception as exc:
        logger.error("Error extracting metadata from %s: %s", path, exc)
        if not metadata:
            add_common_file_metadata(metadata, path)

    return metadata


__all__ = [
    "MEDIA_TYPE_EXTRACTORS",
    "_best_creation_timestamp",
    "detect_media_type",
    "extract_metadata",
]
