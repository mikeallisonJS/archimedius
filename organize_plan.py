#!/usr/bin/env python3
"""
Headless source scan and destination path planning for Archimedius.

Preview and organize runs share this module for recursive source scan rules
and template-based destination path resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from media_file import MediaFile

MediaFileFactory = Callable[[Path, Mapping[str, Sequence[str]]], MediaFile]


@dataclass(frozen=True)
class FilePlan:
    """A planned organize operation for one file."""

    source_path: Path
    destination_path: str
    media_type: str


@dataclass(frozen=True)
class ScanResult:
    """Outcome of scanning a source and building file plans."""

    plans: list[FilePlan]
    total_count: int


def all_supported_extensions(supported_extensions: Mapping[str, Sequence[str]]) -> set[str]:
    """Return the union of every configured extension (lowercase, with dot)."""
    extensions: set[str] = set()
    for extension_list in supported_extensions.values():
        extensions.update(ext.lower() for ext in extension_list)
    return extensions


def normalize_selected_extensions(selected_extensions: Iterable[str]) -> set[str]:
    """Normalize extension strings for comparison."""
    return {ext.lower() for ext in selected_extensions}


def is_recognized_extension(
    suffix: str, supported_extensions: Mapping[str, Sequence[str]]
) -> bool:
    """Return True when the suffix belongs to a configured media type."""
    return suffix.lower() in all_supported_extensions(supported_extensions)


def is_destination_inside_source(source: Path, destination: Path | None) -> bool:
    """Return True when destination is a strict subdirectory of source."""
    if destination is None:
        return False

    try:
        abs_source = source.resolve()
        abs_destination = destination.resolve()
        if abs_destination == abs_source:
            return False
        abs_destination.relative_to(abs_source)
        return True
    except (ValueError, OSError):
        return False


def should_skip_file_under_destination(
    file_path: Path,
    source: Path,
    destination: Path,
    *,
    dest_in_source: bool,
) -> bool:
    """Return True when a file lives under the destination tree inside source."""
    if not dest_in_source or not file_path.is_file():
        return False

    try:
        return file_path.is_relative_to(destination)
    except ValueError:
        return False


def iter_matching_files(
    source: Path,
    *,
    selected_extensions: Iterable[str],
    supported_extensions: Mapping[str, Sequence[str]],
    destination: Path | None = None,
) -> list[Path]:
    """
    Recursively scan source and return matching file paths in walk order.

    Files are skipped when:
    - not a regular file
    - extension is not in selected_extensions
    - extension is unrecognized (not in supported_extensions)
    - file is under destination while destination is inside source
    """
    selected = normalize_selected_extensions(selected_extensions)
    recognized = all_supported_extensions(supported_extensions)
    dest_in_source = is_destination_inside_source(source, destination)
    matches: list[Path] = []

    for file_path in source.rglob("*"):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix not in selected:
            continue

        if suffix not in recognized:
            continue

        if destination is not None and should_skip_file_under_destination(
            file_path,
            source,
            destination,
            dest_in_source=dest_in_source,
        ):
            continue

        matches.append(file_path)

    return matches


def build_file_plan(
    file_path: Path,
    *,
    templates: Mapping[str, str],
    supported_extensions: Mapping[str, Sequence[str]],
    exclude_unknown: Mapping[str, bool],
    media_file_factory: MediaFileFactory = MediaFile,
) -> FilePlan:
    """Build a destination path plan for a single source file."""
    media_file = media_file_factory(file_path, supported_extensions)
    template = templates.get(media_file.file_type, templates.get("audio", "{filename}"))
    exclude = exclude_unknown.get(media_file.file_type, False)
    destination_path = media_file.get_formatted_path(template, exclude_unknown=exclude)

    return FilePlan(
        source_path=file_path,
        destination_path=destination_path,
        media_type=media_file.file_type,
    )


def scan_source(
    source: str | Path,
    destination: str | Path | None,
    templates: Mapping[str, str],
    supported_extensions: Mapping[str, Sequence[str]],
    selected_extensions: Iterable[str],
    exclude_unknown: Mapping[str, bool],
    *,
    max_files: int | None = None,
    media_file_factory: MediaFileFactory = MediaFile,
) -> ScanResult:
    """
    Scan source and produce file plans with computed destination paths.

    Args:
        source: Root folder to scan recursively.
        destination: Destination root (used to skip files already organized there).
        templates: Per-media-type path templates.
        supported_extensions: Full extension lists by media type.
        selected_extensions: Subset of extensions to include in this run.
        exclude_unknown: Per-media-type exclude-unknown flags.
        max_files: Optional cap on returned plans (total_count is still complete).
        media_file_factory: Injectable factory for tests.

    Returns:
        ScanResult with plans (possibly limited) and total matching file count.
    """
    source_path = Path(source)
    destination_path = Path(destination) if destination else None

    matching_files = iter_matching_files(
        source_path,
        selected_extensions=selected_extensions,
        supported_extensions=supported_extensions,
        destination=destination_path,
    )

    total_count = len(matching_files)
    if max_files is not None:
        matching_files = matching_files[:max_files]

    plans = [
        build_file_plan(
            file_path,
            templates=templates,
            supported_extensions=supported_extensions,
            exclude_unknown=exclude_unknown,
            media_file_factory=media_file_factory,
        )
        for file_path in matching_files
    ]

    return ScanResult(plans=plans, total_count=total_count)
