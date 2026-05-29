"""Image metadata extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger("MediaOrganizer")


def extract_image_metadata(file_path: Path, metadata: dict) -> None:
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
