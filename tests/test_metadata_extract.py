#!/usr/bin/env python3
"""
Unit tests for metadata extraction by media type.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import defaults
import pytest
from PIL import Image

from metadata_extract import detect_media_type, extract_metadata
from tests.conftest import write_minimal_epub

SUPPORTED = defaults.DEFAULT_EXTENSIONS


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

    with patch("metadata_extract.audio.TinyTag.get", return_value=tag):
        metadata = extract_metadata(audio_path, media_type="audio")

    assert metadata["title"] == "Test Song"
    assert metadata["artist"] == "Test Artist"
    assert metadata["genre"] == "Rock"
    assert metadata["filename_with_extension"] == "song.mp3"
    assert metadata["extension"] == "mp3"


def test_extract_metadata_audio_defaults_when_tag_read_fails(tmp_path: Path):
    audio_path = tmp_path / "broken.mp3"
    audio_path.write_bytes(b"")

    with patch("metadata_extract.audio.TinyTag.get", side_effect=OSError("read failed")):
        metadata = extract_metadata(audio_path, media_type="audio")

    assert metadata["title"] == "broken"
    assert metadata["artist"] == "Unknown"
    assert metadata["genre"] == "Unknown"


def test_extract_metadata_video_uses_mediainfo_when_available(tmp_path: Path):
    video_path = tmp_path / "movie.mkv"
    video_path.write_bytes(b"")

    general_track = MagicMock(
        track_type="General",
        title="Feature Film",
        movie_name=None,
        album=None,
        performer="Lead Actor",
        director="Famous Director",
        recorded_date="2019-06-01",
        genre="Drama",
        duration=125000,
    )
    video_track = MagicMock(
        track_type="Video",
        width=1920,
        height=1080,
        frame_rate="24.000",
        codec="AVC",
        bit_depth=8,
    )
    media_info = MagicMock(tracks=[general_track, video_track])

    with (
        patch("metadata_extract.video.MEDIAINFO_AVAILABLE", True),
        patch("metadata_extract.video.MediaInfo.parse", return_value=media_info),
    ):
        metadata = extract_metadata(video_path, media_type="video")

    assert metadata["title"] == "Feature Film"
    assert metadata["artist"] == "Lead Actor"
    assert metadata["year"] == "2019"
    assert metadata["width"] == 1920
    assert metadata["duration"] == "2:05"


def test_extract_metadata_video_falls_back_when_mediainfo_unavailable(tmp_path: Path):
    video_path = tmp_path / "clip.mp4"
    video_path.write_bytes(b"x" * 32)

    tag = MagicMock(title="Fallback Title", artist=None, year=2021, duration=90.0)

    with (
        patch("metadata_extract.video.MEDIAINFO_AVAILABLE", False),
        patch("metadata_extract.video.TinyTag.get", return_value=tag),
    ):
        metadata = extract_metadata(video_path, media_type="video")

    assert metadata["title"] == "Fallback Title"
    assert metadata["year"] == "2021"
    assert metadata["duration"] == "1:30"
    assert metadata["filename"] == "clip"


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


def test_extract_metadata_epub_reads_dc_fields(tmp_path: Path):
    epub_path = tmp_path / "book.epub"
    write_minimal_epub(epub_path)

    metadata = extract_metadata(epub_path, media_type="ebook")

    assert metadata["title"] == "Sample Book"
    assert metadata["author"] == "Jane Author"
    assert metadata["year"] == "2022"
    assert metadata["publisher"] == "Test Press"
    assert metadata["language"] == "en"


def test_extract_metadata_pdf_graceful_when_pypdf_missing(tmp_path: Path):
    pdf_path = tmp_path / "doc.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    with patch.dict("sys.modules", {"pypdf": None}):
        metadata = extract_metadata(pdf_path, media_type="ebook")

    assert metadata["title"] == "doc"
    assert metadata["author"] == "Unknown"


def test_best_creation_timestamp_prefers_birthtime_on_macos(monkeypatch):
    from metadata_extract import _best_creation_timestamp

    class FakeStat:
        st_ctime = 100.0
        st_mtime = 200.0
        st_birthtime = 50.0

    monkeypatch.setattr("metadata_extract.common.sys.platform", "darwin")
    assert _best_creation_timestamp(FakeStat()) == 50.0


def test_best_creation_timestamp_uses_ctime_on_windows(monkeypatch):
    from metadata_extract import _best_creation_timestamp

    class FakeStat:
        st_ctime = 100.0
        st_mtime = 200.0

    monkeypatch.setattr("metadata_extract.common.sys.platform", "win32")
    assert _best_creation_timestamp(FakeStat()) == 100.0


def test_best_creation_timestamp_falls_back_to_mtime_on_linux(monkeypatch):
    from metadata_extract import _best_creation_timestamp

    class FakeStat:
        st_ctime = 100.0
        st_mtime = 200.0

    monkeypatch.setattr("metadata_extract.common.sys.platform", "linux")
    assert _best_creation_timestamp(FakeStat()) == 200.0


def test_extract_metadata_requires_supported_extensions_when_type_omitted(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    audio_path.write_bytes(b"")

    with pytest.raises(ValueError, match="supported_extensions is required"):
        extract_metadata(audio_path)
