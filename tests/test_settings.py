#!/usr/bin/env python3
"""Tests for Settings load/save round-trip without the GUI."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import copy
import defaults
from settings import Settings, configure_logging, default_settings, load_settings, save_settings


def test_default_settings_matches_application_defaults():
    settings = default_settings()
    assert settings.templates == defaults.DEFAULT_TEMPLATES
    assert settings.logging_level == defaults.DEFAULT_SETTINGS["logging_level"]
    assert settings.exclude_unknown == defaults.DEFAULT_EXCLUDE_UNKNOWN
    assert all(settings.extension_selections[media_type] for media_type in settings.extension_selections)


def test_settings_round_trip_via_dict():
    original = Settings(
        source_dir="/media/in",
        output_dir="/media/out",
        templates={
            "audio": "{year}/{artist}/{filename}",
            "video": "{year}/{filename}",
            "image": "{year}/{filename}",
            "ebook": "{author}/{title}/{filename}",
        },
        supported_extensions={
            "audio": [".mp3", ".flac"],
            "video": [".mp4"],
            "image": [".jpg"],
            "ebook": [".epub"],
        },
        extension_selections={
            "audio": {".mp3": True, ".flac": False},
            "video": {".mp4": True},
            "image": {".jpg": True},
            "ebook": {".epub": False},
        },
        exclude_unknown={"audio": False, "video": True, "image": True, "ebook": False},
        operation_mode="move",
        show_full_paths=True,
        auto_save_enabled=False,
        auto_preview_enabled=False,
        logging_level="DEBUG",
        dark_mode=True,
        window_geometry="900x900",
        collision_policy="rename",
    )

    restored = Settings.from_dict(original.to_dict())

    assert restored.source_dir == original.source_dir
    assert restored.output_dir == original.output_dir
    assert restored.templates == original.templates
    assert restored.supported_extensions == original.supported_extensions
    assert restored.extension_selections == original.extension_selections
    assert restored.exclude_unknown == original.exclude_unknown
    assert restored.operation_mode == original.operation_mode
    assert restored.show_full_paths == original.show_full_paths
    assert restored.auto_save_enabled == original.auto_save_enabled
    assert restored.auto_preview_enabled == original.auto_preview_enabled
    assert restored.logging_level == original.logging_level
    assert restored.dark_mode == original.dark_mode
    assert restored.window_geometry == original.window_geometry
    assert restored.collision_policy == original.collision_policy


def test_load_save_round_trip_file(tmp_path):
    config_file = tmp_path / "archimedius_settings.json"
    settings = Settings(
        source_dir="/src",
        output_dir="/dest",
        logging_level="WARNING",
        supported_extensions={"audio": [".wav"], "video": [], "image": [], "ebook": []},
    )
    settings.supported_extensions["video"] = defaults.DEFAULT_EXTENSIONS["video"]
    settings.supported_extensions["image"] = defaults.DEFAULT_EXTENSIONS["image"]
    settings.supported_extensions["ebook"] = defaults.DEFAULT_EXTENSIONS["ebook"]

    save_settings(settings, config_file)
    loaded = load_settings(config_file)

    assert loaded.source_dir == "/src"
    assert loaded.output_dir == "/dest"
    assert loaded.logging_level == "WARNING"
    assert loaded.supported_extensions["audio"] == [".wav"]


def test_from_dict_legacy_template_field():
    data = {
        "template": "{year}/legacy/{filename}",
        "custom_extensions": copy.deepcopy(defaults.DEFAULT_EXTENSIONS),
    }
    settings = Settings.from_dict(data)
    assert settings.templates["audio"] == "{year}/legacy/{filename}"


def test_load_missing_file_returns_defaults(tmp_path):
    missing = tmp_path / "missing.json"
    loaded = load_settings(missing)
    assert loaded == default_settings()


def test_default_settings_includes_collision_policy():
    settings = default_settings()
    assert settings.collision_policy == defaults.DEFAULT_SETTINGS["collision_policy"]


def test_from_dict_unknown_collision_policy_falls_back_to_default():
    data = {
        "collision_policy": "invalid",
        "custom_extensions": copy.deepcopy(defaults.DEFAULT_EXTENSIONS),
    }
    settings = Settings.from_dict(data)
    assert settings.collision_policy == defaults.DEFAULT_SETTINGS["collision_policy"]


def test_configure_logging_applies_saved_level(tmp_path, monkeypatch):
    config_file = tmp_path / "archimedius_settings.json"
    save_settings(Settings(logging_level="ERROR"), config_file)
    monkeypatch.setattr("settings.settings_path", lambda: config_file)

    import logging

    logging.basicConfig(level=logging.INFO, force=True)
    configure_logging(load_settings(config_file))

    assert logging.getLogger("Archimedius").level == defaults.LOGGING_LEVELS["ERROR"]
