"""Video metadata extraction."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from tinytag import TinyTag

logger = logging.getLogger("MediaOrganizer")

try:
    from pymediainfo import MediaInfo

    MEDIAINFO_AVAILABLE = True
except (ImportError, OSError):
    MEDIAINFO_AVAILABLE = False
    logging.warning(
        "pymediainfo or MediaInfo not available. Video metadata extraction will be limited."
    )


def extract_video_metadata(file_path: Path, metadata: dict) -> None:
    """Extract metadata from video files."""
    metadata["title"] = file_path.stem

    if MEDIAINFO_AVAILABLE:
        try:
            media_info = MediaInfo.parse(file_path)

            for track in media_info.tracks:
                if track.track_type == "General":
                    if hasattr(track, "title") and track.title:
                        metadata["title"] = track.title
                    if hasattr(track, "movie_name") and track.movie_name:
                        metadata["title"] = track.movie_name
                    if hasattr(track, "album") and track.album:
                        metadata["album"] = track.album
                    if hasattr(track, "performer") and track.performer:
                        metadata["artist"] = track.performer
                    if hasattr(track, "director") and track.director:
                        metadata["director"] = track.director
                    if hasattr(track, "recorded_date") and track.recorded_date:
                        metadata["year"] = track.recorded_date[:4]
                    if hasattr(track, "genre") and track.genre:
                        metadata["genre"] = track.genre
                    if hasattr(track, "duration") and track.duration:
                        duration_ms = float(track.duration)
                        minutes = int(duration_ms / 60000)
                        seconds = int((duration_ms % 60000) / 1000)
                        metadata["duration"] = f"{minutes}:{seconds:02d}"

                elif track.track_type == "Video":
                    if hasattr(track, "width") and track.width:
                        metadata["width"] = track.width
                    if hasattr(track, "height") and track.height:
                        metadata["height"] = track.height
                    if hasattr(track, "frame_rate") and track.frame_rate:
                        metadata["frame_rate"] = track.frame_rate
                    if hasattr(track, "codec") and track.codec:
                        metadata["codec"] = track.codec
                    if hasattr(track, "bit_depth") and track.bit_depth:
                        metadata["bit_depth"] = track.bit_depth

            logger.info("Extracted video metadata for %s", file_path)
        except Exception as exc:
            logger.error("Error extracting video metadata: %s", exc)
    else:
        logger.warning("MediaInfo not available. Limited metadata for %s", file_path)
        metadata["year"] = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y")

        try:
            tag = TinyTag.get(file_path)

            if tag.title:
                metadata["title"] = tag.title
            if tag.artist:
                metadata["artist"] = tag.artist
            if tag.year:
                metadata["year"] = str(tag.year)
            if tag.duration:
                minutes = int(tag.duration // 60)
                seconds = int(tag.duration % 60)
                metadata["duration"] = f"{minutes}:{seconds:02d}"
        except Exception:
            pass
