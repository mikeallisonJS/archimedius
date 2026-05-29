#!/usr/bin/env python3
"""
Unit tests for build_file_plan type detection and path formatting behavior.
"""

import os
from pathlib import Path

import defaults
from metadata_extract import detect_media_type, extract_metadata
from organize_plan import build_file_plan

SUPPORTED = defaults.DEFAULT_EXTENSIONS
TEMPLATES = defaults.DEFAULT_TEMPLATES.copy()
EXCLUDE_UNKNOWN_OFF = {media_type: False for media_type in SUPPORTED}
EXCLUDE_UNKNOWN_ON = {media_type: True for media_type in SUPPORTED}


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


def test_detects_file_type_case_insensitive_extension(tmp_path: Path):
    audio_path = tmp_path / "Track.MP3"
    _touch(audio_path)

    media_type = detect_media_type(audio_path, SUPPORTED)
    metadata = extract_metadata(
        audio_path,
        media_type=media_type,
        supported_extensions=SUPPORTED,
    )

    assert media_type == "audio"
    assert metadata["extension"] == "mp3"
    assert metadata["filename_with_extension"] == "Track.MP3"


def test_build_file_plan_unknown_extension_maps_to_unknown_type(tmp_path: Path):
    file_path = tmp_path / "notes.xyz"
    _touch(file_path)

    media_type = detect_media_type(file_path, SUPPORTED)
    metadata = extract_metadata(
        file_path,
        media_type=media_type,
        supported_extensions=SUPPORTED,
    )
    plan = build_file_plan(
        file_path,
        templates=TEMPLATES,
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    assert media_type == "unknown"
    assert metadata["filename"] == "notes"
    assert plan.media_type == "unknown"


def test_build_file_plan_sanitizes_reserved_characters_in_metadata(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    _touch(audio_path)

    def stub_metadata_extractor(file_path, supported_extensions):
        return "audio", {
            "artist": 'AC/DC:Live*Band?',
            "title": 'Hit<>:"Song"|',
            "filename_with_extension": "song.mp3",
            "extension": "mp3",
        }

    plan = build_file_plan(
        audio_path,
        templates={"audio": "{artist}/{title}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        metadata_extractor=stub_metadata_extractor,
    )

    assert "AC_DC_Live_Band_" in plan.destination_path
    assert "Hit____Song__" in plan.destination_path
    assert plan.destination_path.endswith(os.path.join("Hit____Song__", "song.mp3"))


def test_build_file_plan_exclude_unknown_removes_unknown_segments(tmp_path: Path):
    image_path = tmp_path / "cover.jpg"
    _touch(image_path)

    def stub_metadata_extractor(file_path, supported_extensions):
        return "image", {
            "filename_with_extension": "cover.jpg",
            "extension": "jpg",
        }

    plan = build_file_plan(
        image_path,
        templates={"image": "{camera_make}/{camera_model}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_ON,
        metadata_extractor=stub_metadata_extractor,
    )

    assert "Unknown" not in plan.destination_path
    assert plan.destination_path == os.path.join("image", "cover.jpg")


def test_build_file_plan_adds_extension_when_template_has_filename_only(tmp_path: Path):
    video_path = tmp_path / "clip.mp4"
    _touch(video_path)

    def stub_metadata_extractor(file_path, supported_extensions):
        return "video", {"filename": "clip", "extension": "mp4"}

    plan = build_file_plan(
        video_path,
        templates={"video": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        metadata_extractor=stub_metadata_extractor,
    )

    assert plan.destination_path == "clip.mp4"
