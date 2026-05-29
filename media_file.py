#!/usr/bin/env python3
"""
Media File module for Archimedius application.

Thin wrapper around metadata extraction and destination path resolution.
"""

from pathlib import Path

from destination_path import resolve_destination_path
from metadata_extract import detect_media_type, extract_metadata


class MediaFile:
    """Class to represent a media file with its metadata."""

    def __init__(self, file_path, supported_extensions):
        """
        Initialize a MediaFile object.

        Args:
            file_path: Path to the media file
            supported_extensions: Dictionary of supported file extensions by media type
        """
        self.file_path = Path(file_path)
        self.supported_extensions = supported_extensions
        self.file_type = detect_media_type(self.file_path, supported_extensions)
        self.metadata = extract_metadata(
            self.file_path,
            media_type=self.file_type,
            supported_extensions=supported_extensions,
        )

    def extract_metadata(self):
        """Re-extract metadata from the media file."""
        self.metadata = extract_metadata(
            self.file_path,
            media_type=self.file_type,
            supported_extensions=self.supported_extensions,
        )

    def get_formatted_path(self, template, exclude_unknown=False):
        """
        Format the destination path using the template and metadata.

        Args:
            template: String template with placeholders for metadata fields
            exclude_unknown: If True, removes "Unknown" folders from the path

        Returns:
            Formatted path string
        """
        return resolve_destination_path(
            self.metadata,
            self.file_type,
            template,
            exclude_unknown=exclude_unknown,
        )
