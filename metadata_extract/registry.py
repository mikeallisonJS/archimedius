"""Registry mapping media types to metadata extractors."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from metadata_extract.audio import extract_audio_metadata
from metadata_extract.ebook import extract_ebook_metadata
from metadata_extract.image import extract_image_metadata
from metadata_extract.video import extract_video_metadata

MediaTypeExtractor = Callable[[Path, dict], None]

MEDIA_TYPE_EXTRACTORS: dict[str, MediaTypeExtractor] = {
    "audio": extract_audio_metadata,
    "video": extract_video_metadata,
    "image": extract_image_metadata,
    "ebook": extract_ebook_metadata,
}
