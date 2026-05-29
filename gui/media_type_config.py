"""Shared media-type labels and template examples for GUI panels."""

from settings import MEDIA_TYPES

MEDIA_TYPE_SECTIONS: tuple[tuple[str, str, str], ...] = (
    ("audio", "Audio", "All Audio"),
    ("video", "Video", "All Video"),
    ("image", "Image", "All Images"),
    ("ebook", "eBook", "All eBooks"),
)

TEMPLATE_EXAMPLES: dict[str, str] = {
    "audio": "{file_type}/{artist}/{album}/{filename}",
    "video": "{file_type}/{year}/{filename}",
    "image": "{file_type}/{creation_year}/{creation_month_name}/{filename}",
    "ebook": "{file_type}/{author}/{title}/{filename}",
}

MEDIA_TYPE_TAB_LABELS: dict[str, str] = {
    media_type: title for media_type, title, _ in MEDIA_TYPE_SECTIONS
}

__all__ = ["MEDIA_TYPES", "MEDIA_TYPE_SECTIONS", "MEDIA_TYPE_TAB_LABELS", "TEMPLATE_EXAMPLES"]
