#!/usr/bin/env python3
"""
Unit tests for metadata extraction by media type.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import extensions
import pytest
from PIL import Image

from metadata_extract import detect_media_type, extract_metadata

SUPPORTED = extensions.DEFAULT_EXTENSIONS


def test_detect_media_type_case_insensitive():
    assert detect_media_type("Track.MP3", SUPPORTED) == "audio"
    assert detect_media_type("notes.xyz", SUPPORTED) == "unknown"


def test_extract_metadata_audio_without_path_resolution(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    audio_path.write_bytes(b"")

    tag = MagicMock(
        title="Test Song",
        artist="Test Artist",
        album="Test Album",
        year=2020,
        genre="Rock",
        track=1,
        duration=125.0,
        bitrate=320000,
        samplerate=44100,
    )

    with patch("metadata_extract.TinyTag.get", return_value=tag):
        metadata = extract_metadata(audio_path, media_type="audio")

    assert metadata["title"] == "Test Song"
    assert metadata["artist"] == "Test Artist"
    assert metadata["genre"] == "Rock"
    assert metadata["filename_with_extension"] == "song.mp3"
    assert metadata["extension"] == "mp3"


def test_extract_metadata_audio_defaults_when_tag_read_fails(tmp_path: Path):
    audio_path = tmp_path / "broken.mp3"
    audio_path.write_bytes(b"")

    with patch("metadata_extract.TinyTag.get", side_effect=OSError("read failed")):
        metadata = extract_metadata(audio_path, media_type="audio")

    assert metadata["title"] == "broken"
    assert metadata["artist"] == "Unknown"
    assert metadata["genre"] == "Unknown"


def test_extract_metadata_image_reads_dimensions(tmp_path: Path):
    image_path = tmp_path / "photo.jpg"
    Image.new("RGB", (640, 480), color="red").save(image_path, format="JPEG")

    metadata = extract_metadata(image_path, media_type="image")

    assert metadata["width"] == 640
    assert metadata["height"] == 480
    assert metadata["format"] == "JPEG"
    assert metadata["filename_with_extension"] == "photo.jpg"


def test_extract_metadata_image_without_exif_leaves_camera_fields_absent(tmp_path: Path):
    image_path = tmp_path / "plain.png"
    Image.new("RGBA", (10, 10), color=(0, 0, 0, 0)).save(image_path, format="PNG")

    metadata = extract_metadata(image_path, media_type="image")

    assert "camera_make" not in metadata
    assert metadata["extension"] == "png"


def test_extract_metadata_requires_supported_extensions_when_type_omitted(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    audio_path.write_bytes(b"")

    with pytest.raises(ValueError, match="supported_extensions is required"):
        extract_metadata(audio_path)
