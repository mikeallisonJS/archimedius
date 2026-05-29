"""Audio metadata extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from tinytag import TinyTag

logger = logging.getLogger("MediaOrganizer")


def extract_audio_metadata(file_path: Path, metadata: dict) -> None:
    """Extract metadata from audio files using TinyTag."""
    metadata.update(
        {
            "title": file_path.stem,
            "artist": "Unknown",
            "album": "Unknown",
            "year": "Unknown",
            "genre": "Unknown",
            "track": "Unknown",
            "duration": "Unknown",
            "bitrate": "Unknown",
            "sample_rate": "Unknown",
        }
    )

    try:
        tag = TinyTag.get(file_path)

        if tag.title:
            metadata["title"] = tag.title
        if tag.artist:
            metadata["artist"] = tag.artist
        if tag.album:
            metadata["album"] = tag.album
        if tag.year:
            metadata["year"] = str(tag.year)
        if tag.genre:
            metadata["genre"] = tag.genre
        if tag.track:
            metadata["track"] = str(tag.track)

        if tag.duration:
            minutes = int(tag.duration // 60)
            seconds = int(tag.duration % 60)
            metadata["duration"] = f"{minutes}:{seconds:02d}"
        if tag.bitrate:
            metadata["bitrate"] = f"{int(tag.bitrate)} kbps"
        if tag.samplerate:
            metadata["sample_rate"] = f"{int(tag.samplerate / 1000)} kHz"

        logger.info("Extracted audio metadata for %s", file_path)

    except Exception as exc:
        logger.error("Error in audio metadata extraction for %s: %s", file_path, exc)
        if "title" not in metadata:
            metadata["title"] = file_path.stem
