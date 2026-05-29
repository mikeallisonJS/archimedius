#!/usr/bin/env python3
"""
Destination path resolution for Archimedius.

Pure functions that map metadata and templates to relative destination paths.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Mapping

logger = logging.getLogger("MediaOrganizer")


def resolve_destination_path(
    metadata: Mapping[str, object],
    media_type: str,
    template: str,
    *,
    exclude_unknown: bool = False,
) -> str:
    """
    Resolve a relative destination path from metadata and a template.

    Args:
        metadata: Extracted metadata fields for the file.
        media_type: Detected media type (audio, video, image, ebook, unknown).
        template: Relative path template with {placeholder} tokens.
        exclude_unknown: When True, omit path segments produced from missing metadata.

    Returns:
        Relative destination path string.
    """
    try:
        formatted_path = template
        resolved_metadata = dict(metadata)
        resolved_metadata["file_type"] = media_type

        for key, value in resolved_metadata.items():
            placeholder = "{" + key + "}"
            if placeholder in formatted_path:
                str_value = str(value)
                sanitized = re.sub(r'[<>:"/\\|?*]', "_", str_value)
                formatted_path = formatted_path.replace(placeholder, sanitized)

        formatted_path = re.sub(r"{[^{}]+}", "Unknown", formatted_path)

        if exclude_unknown:
            path_parts = re.split(r"[\\/]+", formatted_path)
            path_parts = [part for part in path_parts if part != "Unknown"]
            formatted_path = os.sep.join(path_parts)
            if not formatted_path:
                formatted_path = media_type

        filename_with_extension = str(resolved_metadata.get("filename_with_extension", ""))
        extension = str(resolved_metadata.get("extension", ""))

        if "{filename}" not in template and "{extension}" not in template:
            formatted_path = os.path.join(formatted_path, filename_with_extension)
        elif "{filename}" in template and "{extension}" not in template:
            base_dir = os.path.dirname(formatted_path)
            base_name = os.path.basename(formatted_path)
            expected_suffix = f".{extension.lower()}"
            if not base_name.lower().endswith(expected_suffix):
                base_name = f"{base_name}.{extension}"
                formatted_path = os.path.join(base_dir, base_name) if base_dir else base_name

        return os.path.normpath(formatted_path)

    except Exception as exc:
        logger.error("Error formatting path: %s", exc)
        filename_with_extension = str(metadata.get("filename_with_extension", "file"))
        return os.path.join(media_type, filename_with_extension)
