#!/usr/bin/env python3
"""
Unit tests for pure destination path resolution.
"""

import os

from destination_path import resolve_destination_path


def test_resolve_destination_path_sanitizes_reserved_characters_in_metadata():
    metadata = {
        "artist": 'AC/DC:Live*Band?',
        "title": 'Hit<>:"Song"|',
        "filename_with_extension": "song.mp3",
        "extension": "mp3",
    }

    formatted = resolve_destination_path(
        metadata,
        "audio",
        "{artist}/{title}",
    )

    assert "AC_DC_Live_Band_" in formatted
    assert "Hit____Song__" in formatted
    assert formatted.endswith(os.path.join("Hit____Song__", "song.mp3"))


def test_resolve_destination_path_exclude_unknown_removes_unknown_segments():
    metadata = {
        "filename_with_extension": "cover.jpg",
        "extension": "jpg",
    }

    formatted = resolve_destination_path(
        metadata,
        "image",
        "{camera_make}/{camera_model}",
        exclude_unknown=True,
    )

    assert "Unknown" not in formatted
    assert formatted == os.path.join("image", "cover.jpg")


def test_resolve_destination_path_exclude_unknown_with_forward_slash_template():
    metadata = {
        "filename_with_extension": "track.mp3",
        "extension": "mp3",
    }

    formatted = resolve_destination_path(
        metadata,
        "audio",
        "{genre}/{artist}/{title}",
        exclude_unknown=True,
    )

    assert "Unknown" not in formatted
    assert formatted == os.path.join("audio", "track.mp3")


def test_resolve_destination_path_fills_missing_placeholders_with_unknown():
    metadata = {
        "filename": "song",
        "filename_with_extension": "song.mp3",
        "extension": "mp3",
    }

    formatted = resolve_destination_path(
        metadata,
        "audio",
        "{genre}/{filename}",
    )

    assert formatted.startswith(os.path.join("Unknown", "song"))


def test_resolve_destination_path_adds_extension_when_template_has_filename_only():
    metadata = {"filename": "clip", "extension": "mp4", "filename_with_extension": "clip.mp4"}

    formatted = resolve_destination_path(metadata, "video", "{filename}")

    assert formatted == "clip.mp4"
