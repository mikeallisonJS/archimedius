#!/usr/bin/env python3
"""
Metadata extraction for Archimedius media files.

Extracts embedded tags and file properties without resolving destination paths.
"""

from __future__ import annotations

import logging
import re
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence
from xml.etree import ElementTree as ET

from PIL import Image
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


def _add_common_file_metadata(metadata: dict, file_path: Path) -> None:
    """Add filename, extension, size, and creation date fields."""
    metadata["filename"] = file_path.stem
    metadata["filename_with_extension"] = file_path.name
    metadata["extension"] = file_path.suffix.lower()[1:]

    try:
        stat_result = file_path.stat()
    except OSError:
        return

    creation_time = datetime.fromtimestamp(stat_result.st_ctime)
    metadata["size"] = stat_result.st_size
    metadata["creation_date"] = creation_time.strftime("%Y-%m-%d")
    metadata["creation_year"] = creation_time.strftime("%Y")
    metadata["creation_month"] = creation_time.strftime("%m")
    metadata["creation_month_name"] = creation_time.strftime("%B")


def _extract_audio_metadata(file_path: Path, metadata: dict) -> None:
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


def _extract_video_metadata(file_path: Path, metadata: dict) -> None:
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


def _extract_image_metadata(file_path: Path, metadata: dict) -> None:
    """Extract metadata from image files."""
    try:
        with Image.open(file_path) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode

            if hasattr(img, "_getexif") and img._getexif():
                exif = img._getexif()
                if exif:
                    exif_tags = {
                        271: "camera_make",
                        272: "camera_model",
                        306: "date_time",
                        36867: "date_taken",
                        33432: "copyright",
                    }

                    for tag, value in exif.items():
                        if tag in exif_tags:
                            metadata[exif_tags[tag]] = value

    except Exception as exc:
        logger.error("Error extracting image metadata from %s: %s", file_path, exc)


def _extract_ebook_metadata(file_path: Path, metadata: dict) -> None:
    """Extract metadata from ebook files."""
    metadata.update(
        {
            "title": file_path.stem,
            "author": "Unknown",
            "year": "Unknown",
            "genre": "Unknown",
            "publisher": "Unknown",
            "isbn": "Unknown",
            "language": "Unknown",
        }
    )

    ext = file_path.suffix.lower()

    try:
        if ext == ".pdf":
            try:
                from pypdf import PdfReader

                reader = PdfReader(file_path)
                info = reader.metadata
                if info:
                    if info.get("/Title"):
                        metadata["title"] = info["/Title"]
                    if info.get("/Author"):
                        metadata["author"] = info["/Author"]
                    if info.get("/Producer"):
                        metadata["publisher"] = info["/Producer"]
                    if info.get("/CreationDate"):
                        date_str = info["/CreationDate"]
                        year_match = re.search(r"D:(\d{4})", date_str)
                        if year_match:
                            metadata["year"] = year_match.group(1)
            except ImportError:
                logger.warning("PyPDF not available. Limited PDF metadata extraction.")
            except Exception as exc:
                logger.error("Error extracting PDF metadata from %s: %s", file_path, exc)

        elif ext == ".epub":
            try:
                with zipfile.ZipFile(file_path) as epub:
                    for name in epub.namelist():
                        if name.endswith(".opf"):
                            with epub.open(name) as opf:
                                tree = ET.parse(opf)
                                root = tree.getroot()

                                ns = {
                                    "dc": "http://purl.org/dc/elements/1.1/",
                                    "opf": "http://www.idpf.org/2007/opf",
                                }

                                opf_metadata = root.find(
                                    ".//{http://www.idpf.org/2007/opf}metadata"
                                )
                                if opf_metadata is not None:
                                    title = opf_metadata.find(".//dc:title", ns)
                                    if title is not None and title.text:
                                        metadata["title"] = title.text

                                    creator = opf_metadata.find(".//dc:creator", ns)
                                    if creator is not None and creator.text:
                                        metadata["author"] = creator.text

                                    date = opf_metadata.find(".//dc:date", ns)
                                    if date is not None and date.text:
                                        year_match = re.search(r"\d{4}", date.text)
                                        if year_match:
                                            metadata["year"] = year_match.group(0)

                                    publisher = opf_metadata.find(".//dc:publisher", ns)
                                    if publisher is not None and publisher.text:
                                        metadata["publisher"] = publisher.text

                                    language = opf_metadata.find(".//dc:language", ns)
                                    if language is not None and language.text:
                                        metadata["language"] = language.text

                                    identifier = opf_metadata.find(".//dc:identifier", ns)
                                    if identifier is not None and identifier.text:
                                        scheme = identifier.get(
                                            "{http://www.idpf.org/2007/opf}scheme", ""
                                        ).lower()
                                        if "isbn" in scheme or re.search(
                                            r"isbn", identifier.text, re.I
                                        ):
                                            metadata["isbn"] = identifier.text
                            break
            except Exception as exc:
                logger.error("Error extracting EPUB metadata from %s: %s", file_path, exc)

        elif ext in [".mobi", ".azw", ".azw3"]:
            try:
                import mobi

                book = mobi.Mobi(file_path)
                book.parse()

                if book.title:
                    metadata["title"] = book.title
                if book.author:
                    metadata["author"] = book.author
                if book.publisher:
                    metadata["publisher"] = book.publisher

                if hasattr(book, "publication_date") and book.publication_date:
                    year_match = re.search(r"\d{4}", book.publication_date)
                    if year_match:
                        metadata["year"] = year_match.group(0)

            except ImportError:
                logger.warning("mobi-python not available. Limited MOBI metadata extraction.")
            except Exception as exc:
                logger.error("Error extracting MOBI metadata from %s: %s", file_path, exc)

    except Exception as exc:
        logger.error("Error in ebook metadata extraction for %s: %s", file_path, exc)


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
        if media_type == "audio":
            _extract_audio_metadata(path, metadata)
        elif media_type == "video":
            _extract_video_metadata(path, metadata)
        elif media_type == "image":
            _extract_image_metadata(path, metadata)
        elif media_type == "ebook":
            _extract_ebook_metadata(path, metadata)

        _add_common_file_metadata(metadata, path)
    except Exception as exc:
        logger.error("Error extracting metadata from %s: %s", path, exc)
        if not metadata:
            _add_common_file_metadata(metadata, path)

    return metadata
