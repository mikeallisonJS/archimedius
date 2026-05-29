#!/usr/bin/env python3
"""
Unit tests for headless source scan and destination path planning.
"""

import os
from pathlib import Path
from unittest.mock import patch

import defaults
import pytest

from organize_plan import (
    FilePlan,
    build_file_plan,
    build_plans_for_paths,
    destination_path_is_occupied,
    execute_plans,
    find_unique_destination_path,
    is_destination_inside_source,
    is_recognized_extension,
    iter_matching_files,
    resolve_collision_action,
    resolve_transfer_destination,
    scan_source,
    should_skip_file_under_destination,
    transfer_plan,
)
from destination_path import resolve_destination_path
from metadata_extract import extract_metadata

SUPPORTED = defaults.DEFAULT_EXTENSIONS
TEMPLATES = {
    "audio": "{genre}/{filename}",
    "video": "{filename}",
    "image": "{camera_make}/{filename}",
    "ebook": "{filename}",
}
EXCLUDE_UNKNOWN_OFF = {media_type: False for media_type in SUPPORTED}
EXCLUDE_UNKNOWN_ON = {media_type: True for media_type in SUPPORTED}


def _touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")


@pytest.fixture
def media_tree(tmp_path: Path) -> Path:
    """Source tree with recognized, unrecognized, nested, and dest-nested files."""
    source = tmp_path / "source"
    destination = source / "organized"

    _touch(source / "song.mp3")
    _touch(source / "notes.xyz")
    _touch(source / "nested" / "clip.mp4")
    _touch(destination / "already.mp3")
    _touch(source / "other.flac")

    return source


def test_is_recognized_extension():
    assert is_recognized_extension(".mp3", SUPPORTED) is True
    assert is_recognized_extension(".xyz", SUPPORTED) is False


def test_is_destination_inside_source(tmp_path: Path):
    source = tmp_path / "source"
    nested_dest = source / "dest"
    outside_dest = tmp_path / "outside"
    source.mkdir()
    nested_dest.mkdir()
    outside_dest.mkdir()

    assert is_destination_inside_source(source, nested_dest) is True
    assert is_destination_inside_source(source, source) is False
    assert is_destination_inside_source(source, outside_dest) is False
    assert is_destination_inside_source(source, None) is False


def test_iter_matching_files_filters_selected_extensions(media_tree: Path):
    selected = {".mp3"}

    matches = iter_matching_files(
        media_tree,
        selected_extensions=selected,
        supported_extensions=SUPPORTED,
        destination=media_tree / "organized",
    )

    assert [path.name for path in matches] == ["song.mp3"]


def test_iter_matching_files_skips_unrecognized_extensions(tmp_path: Path):
    source = tmp_path / "source"
    _touch(source / "song.mp3")
    _touch(source / "notes.xyz")
    selected = {".mp3", ".xyz"}

    matches = iter_matching_files(
        source,
        selected_extensions=selected,
        supported_extensions=SUPPORTED,
    )

    assert [path.name for path in matches] == ["song.mp3"]


def test_iter_matching_files_skips_files_under_destination(media_tree: Path):
    selected = {".mp3", ".mp4", ".flac"}
    destination = media_tree / "organized"

    matches = iter_matching_files(
        media_tree,
        selected_extensions=selected,
        supported_extensions=SUPPORTED,
        destination=destination,
    )

    names = {path.name for path in matches}
    assert "already.mp3" not in names
    assert {"song.mp3", "clip.mp4", "other.flac"} <= names


def test_should_skip_file_under_destination(media_tree: Path):
    destination = media_tree / "organized"
    inside = destination / "already.mp3"
    outside = media_tree / "song.mp3"

    assert should_skip_file_under_destination(
        inside,
        media_tree,
        destination,
        dest_in_source=True,
    )
    assert not should_skip_file_under_destination(
        outside,
        media_tree,
        destination,
        dest_in_source=True,
    )


def test_build_file_plan_missing_metadata_uses_unknown_segment(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    _touch(audio_path)

    plan = build_file_plan(
        audio_path,
        templates=TEMPLATES,
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    assert plan.media_type == "audio"
    assert plan.destination_path == os.path.join("Unknown", "song.mp3")


def test_build_file_plan_exclude_unknown_omits_missing_metadata_segment(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    _touch(audio_path)

    plan = build_file_plan(
        audio_path,
        templates=TEMPLATES,
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_ON,
    )

    assert plan.destination_path == "song.mp3"
    assert "Unknown" not in plan.destination_path


def test_scan_source_returns_total_count_beyond_preview_limit(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for index in range(5):
        _touch(source / f"track{index}.mp3")

    result = scan_source(
        source,
        None,
        TEMPLATES,
        SUPPORTED,
        selected_extensions={".mp3"},
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        max_files=2,
    )

    assert result.total_count == 5
    assert len(result.plans) == 2


def test_scan_source_end_to_end_with_custom_plan_hooks(tmp_path: Path):
    source = tmp_path / "source"
    _touch(source / "song.mp3")

    def stub_metadata_extractor(file_path, supported_extensions):
        return "audio", {"filename_with_extension": "song.mp3", "extension": "mp3"}

    def stub_path_resolver(metadata, media_type, template, exclude_unknown=False):
        return "Planned/song.mp3"

    result = scan_source(
        source,
        None,
        TEMPLATES,
        SUPPORTED,
        selected_extensions={".mp3"},
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        metadata_extractor=stub_metadata_extractor,
        path_resolver=stub_path_resolver,
    )

    assert len(result.plans) == 1
    assert result.plans[0].destination_path == "Planned/song.mp3"
    assert result.plans[0].media_type == "audio"


def test_scan_source_uses_shared_destination_path_resolver(tmp_path: Path):
    audio_path = tmp_path / "song.mp3"
    _touch(audio_path)

    metadata = extract_metadata(audio_path, media_type="audio", supported_extensions=SUPPORTED)
    expected = resolve_destination_path(
        metadata,
        "audio",
        "{artist}/{title}",
        exclude_unknown=True,
    )

    plan = build_file_plan(
        audio_path,
        templates={"audio": "{artist}/{title}"},
        supported_extensions=SUPPORTED,
        exclude_unknown={"audio": True},
    )

    assert plan.destination_path == expected


def test_scan_source_raises_when_source_missing(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="does not exist"):
        scan_source(
            missing,
            None,
            TEMPLATES,
            SUPPORTED,
            selected_extensions={".mp3"},
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        )


def test_scan_source_raises_when_source_is_not_directory(tmp_path: Path):
    file_path = tmp_path / "not-a-dir.mp3"
    _touch(file_path)

    with pytest.raises(ValueError, match="not a directory"):
        scan_source(
            file_path,
            None,
            TEMPLATES,
            SUPPORTED,
            selected_extensions={".mp3"},
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        )


def test_iter_matching_files_skips_inaccessible_paths(tmp_path: Path):
    source = tmp_path / "source"
    _touch(source / "good.mp3")
    _touch(source / "bad.mp3")
    original_is_file = Path.is_file

    def selective_is_file(self, *args, **kwargs):
        if self.name == "bad.mp3":
            raise PermissionError("access denied")
        return original_is_file(self, *args, **kwargs)

    with patch.object(Path, "is_file", selective_is_file):
        matches = iter_matching_files(
            source,
            selected_extensions={".mp3"},
            supported_extensions=SUPPORTED,
        )

    assert [path.name for path in matches] == ["good.mp3"]


def test_scan_source_raises_when_destination_is_not_directory(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    destination_file = tmp_path / "dest.txt"
    _touch(destination_file)

    with pytest.raises(ValueError, match="Destination path is not a directory"):
        scan_source(
            source,
            destination_file,
            TEMPLATES,
            SUPPORTED,
            selected_extensions={".mp3"},
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        )


def test_scan_source_raises_when_selected_extensions_empty(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(ValueError, match="selected_extensions cannot be empty"):
        scan_source(
            source,
            None,
            TEMPLATES,
            SUPPORTED,
            selected_extensions=[],
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        )


def test_scan_source_raises_when_supported_extensions_empty(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()

    with pytest.raises(ValueError, match="supported_extensions cannot be empty"):
        scan_source(
            source,
            None,
            TEMPLATES,
            {},
            selected_extensions={".mp3"},
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        )


def test_scan_source_raises_when_max_files_negative(tmp_path: Path):
    source = tmp_path / "source"
    _touch(source / "song.mp3")

    with pytest.raises(ValueError, match="max_files must be zero or greater"):
        scan_source(
            source,
            None,
            TEMPLATES,
            SUPPORTED,
            selected_extensions={".mp3"},
            exclude_unknown=EXCLUDE_UNKNOWN_OFF,
            max_files=-1,
        )


def test_iter_matching_files_raises_when_source_missing(tmp_path: Path):
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="does not exist"):
        iter_matching_files(
            missing,
            selected_extensions={".mp3"},
            supported_extensions=SUPPORTED,
        )


def test_transfer_plan_copy_mode_places_file_under_output_root(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    audio_path = source / "song.mp3"
    _touch(audio_path)

    plan = build_file_plan(
        audio_path,
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    destination = transfer_plan(plan, output, "copy")

    assert destination == output / plan.destination_path
    assert destination.is_file()
    assert audio_path.is_file()


def test_transfer_plan_rejects_invalid_operation_mode(tmp_path: Path):
    # Migrated from the former Archimedius.set_operation_mode validation.
    audio_path = tmp_path / "source" / "song.mp3"
    _touch(audio_path)
    plan = build_file_plan(
        audio_path,
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    with pytest.raises(ValueError, match="operation_mode must be 'copy' or 'move'"):
        transfer_plan(plan, tmp_path / "output", "delete")


def test_build_file_plan_falls_back_to_audio_template_for_missing_media_type(
    tmp_path: Path,
):
    # Migrated from the former Archimedius.get_template audio fallback: when the
    # detected media_type has no template, build_file_plan uses the audio one.
    # Force a non-"audio" media_type so the fallback branch is actually taken.
    media_path = tmp_path / "source" / "clip.mp4"
    _touch(media_path)

    def stub_metadata_extractor(file_path, supported_extensions):
        return "video", {"filename_with_extension": "clip.mp4", "extension": "mp4"}

    used_templates = []

    def stub_path_resolver(metadata, media_type, template, exclude_unknown=False):
        used_templates.append(template)
        return "Planned/clip.mp4"

    plan = build_file_plan(
        media_path,
        templates={"audio": "AudioFallback/{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
        metadata_extractor=stub_metadata_extractor,
        path_resolver=stub_path_resolver,
    )

    assert plan.media_type == "video"
    assert used_templates == ["AudioFallback/{filename}"]


def test_execute_plans_copy_mode_end_to_end(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    _touch(source / "song.mp3")
    _touch(source / "clip.mp4")

    scan_result = scan_source(
        source,
        None,
        {"audio": "{filename}", "video": "{filename}"},
        SUPPORTED,
        selected_extensions={".mp3", ".mp4"},
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    organize_result = execute_plans(scan_result.plans, output, operation_mode="copy")

    assert organize_result.attempted == 2
    assert organize_result.successful == 2
    for plan in scan_result.plans:
        assert (output / plan.destination_path).is_file()


def test_execute_plans_move_mode_removes_source_files(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    audio_path = source / "song.mp3"
    _touch(audio_path)

    plans = build_plans_for_paths(
        [audio_path],
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    organize_result = execute_plans(plans, output, operation_mode="move")

    assert organize_result.successful == 1
    assert not audio_path.exists()
    assert (output / plans[0].destination_path).is_file()


def test_execute_plans_honors_should_stop(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    for index in range(3):
        _touch(source / f"track{index}.mp3")

    scan_result = scan_source(
        source,
        None,
        TEMPLATES,
        SUPPORTED,
        selected_extensions={".mp3"},
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )
    stop_after = {"count": 0}

    def should_stop():
        return stop_after["count"] >= 1

    def on_each(_plan, _outcome):
        stop_after["count"] += 1

    organize_result = execute_plans(
        scan_result.plans,
        output,
        operation_mode="copy",
        should_stop=should_stop,
        on_each=on_each,
    )

    assert organize_result.stopped_early is True
    assert organize_result.attempted == 1
    assert organize_result.successful == 1


def test_find_unique_destination_path_appends_counter(tmp_path: Path):
    destination = tmp_path / "song.mp3"
    _touch(destination)

    renamed = find_unique_destination_path(destination, set())

    assert renamed == tmp_path / "song (1).mp3"


def test_find_unique_destination_path_avoids_in_run_occupancy(tmp_path: Path):
    destination = tmp_path / "song.mp3"
    _touch(destination)
    occupied = {(tmp_path / "song (1).mp3").resolve()}

    renamed = find_unique_destination_path(destination, occupied)

    assert renamed == tmp_path / "song (2).mp3"


def test_resolve_collision_action_maps_policies():
    assert resolve_collision_action(defaults.COLLISION_POLICY_RENAME) == "rename"
    assert resolve_collision_action(defaults.COLLISION_POLICY_OVERWRITE) == "overwrite"
    assert resolve_collision_action(defaults.COLLISION_POLICY_SKIP) == "skip"


def test_resolve_transfer_destination_skips_when_policy_is_skip(tmp_path: Path):
    destination = tmp_path / "song.mp3"
    _touch(destination)

    resolved, action = resolve_transfer_destination(
        destination,
        policy=defaults.COLLISION_POLICY_SKIP,
        occupied_paths=set(),
    )

    assert resolved is None
    assert action == "skip"


def test_execute_plans_rename_policy_avoids_overwrite(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    first_source = source / "a.mp3"
    second_source = source / "b.mp3"
    _touch(first_source)
    _touch(second_source)

    plans = [
        FilePlan(first_source, "song.mp3", "audio"),
        FilePlan(second_source, "song.mp3", "audio"),
    ]

    organize_result = execute_plans(
        plans,
        output,
        operation_mode="copy",
        collision_policy=defaults.COLLISION_POLICY_RENAME,
    )

    assert organize_result.successful == 2
    assert (output / "song.mp3").is_file()
    assert (output / "song (1).mp3").is_file()


def test_execute_plans_skip_policy_leaves_existing_file(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    existing = output / "song.mp3"
    incoming = source / "song.mp3"
    _touch(existing)
    existing.write_bytes(b"original")
    _touch(incoming)
    incoming.write_bytes(b"new")

    plans = build_plans_for_paths(
        [incoming],
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    organize_result = execute_plans(
        plans,
        output,
        operation_mode="copy",
        collision_policy=defaults.COLLISION_POLICY_SKIP,
    )

    assert organize_result.attempted == 1
    assert organize_result.successful == 0
    assert organize_result.outcomes[0].skipped is True
    assert existing.read_bytes() == b"original"


def test_execute_plans_overwrite_policy_replaces_existing_file(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    existing = output / "song.mp3"
    incoming = source / "song.mp3"
    _touch(existing)
    existing.write_bytes(b"original")
    _touch(incoming)
    incoming.write_bytes(b"replacement")

    plans = build_plans_for_paths(
        [incoming],
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    organize_result = execute_plans(
        plans,
        output,
        operation_mode="copy",
        collision_policy=defaults.COLLISION_POLICY_OVERWRITE,
    )

    assert organize_result.successful == 1
    assert existing.read_bytes() == b"replacement"


def test_execute_plans_prompt_policy_uses_resolver(tmp_path: Path):
    source = tmp_path / "source"
    output = tmp_path / "output"
    existing = output / "song.mp3"
    incoming = source / "song.mp3"
    _touch(existing)
    _touch(incoming)

    plans = build_plans_for_paths(
        [incoming],
        templates={"audio": "{filename}"},
        supported_extensions=SUPPORTED,
        exclude_unknown=EXCLUDE_UNKNOWN_OFF,
    )

    def resolver(_plan, _destination):
        return "rename"

    organize_result = execute_plans(
        plans,
        output,
        operation_mode="copy",
        collision_policy=defaults.COLLISION_POLICY_PROMPT,
        collision_resolver=resolver,
    )

    assert organize_result.successful == 1
    assert (output / "song (1).mp3").is_file()


def test_destination_path_is_occupied_detects_existing_file(tmp_path: Path):
    destination = tmp_path / "song.mp3"
    _touch(destination)

    assert destination_path_is_occupied(destination, set()) is True
    assert destination_path_is_occupied(tmp_path / "missing.mp3", set()) is False
