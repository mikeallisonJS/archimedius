"""
Defaults module for Archimedius.

This module defines all default values used throughout the application.
Centralizing these values makes the application more maintainable and configurable.
"""

import logging

# Application information
APP_NAME = "Archimedius"
APP_VERSION = "0.1.4"
APP_AUTHOR = "Mike Allison"
APP_WEBSITE = "https://mikeallisonjs.com"
APP_EMAIL = "support@mikeallisonjs.com"

# Default supported file extensions for each media type
DEFAULT_EXTENSIONS = {
    "audio": [".mp3", ".flac", ".m4a", ".aac", ".ogg", ".wav"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "ebook": [".epub", ".pdf", ".mobi", ".azw", ".azw3", ".fb2"],
}

# Default templates for each media type
DEFAULT_TEMPLATES = {
    "audio": "{creation_year}/{genre}/{filename}",
    "video": "{creation_year}/{filename}",
    "image": "{creation_year}/{filename}",
    "ebook": "{author}/{title}/{filename}",
}

# Default setting for excluding "Unknown" folders from paths
EXCLUDE_UNKNOWN_DEFAULT = True

# Default exclude unknown settings for each media type
DEFAULT_EXCLUDE_UNKNOWN = {
    "audio": EXCLUDE_UNKNOWN_DEFAULT,
    "video": EXCLUDE_UNKNOWN_DEFAULT,
    "image": EXCLUDE_UNKNOWN_DEFAULT,
    "ebook": EXCLUDE_UNKNOWN_DEFAULT,
}

# Default settings
DEFAULT_SETTINGS = {
    "show_full_paths": False,
    "auto_save_enabled": True,
    "auto_preview_enabled": True,
    "logging_level": "INFO",
    "dark_mode": False,
    "exclude_unknown": DEFAULT_EXCLUDE_UNKNOWN,
}

# Logging levels with user-friendly names
LOGGING_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Default window sizes
DEFAULT_WINDOW_SIZES = {
    "main_window": "800x800",
    "help_window": "600x500",
    "log_window": "600x400",
    "about_dialog": "500x450",
}

# Default file paths
DEFAULT_PATHS = {
    "settings_file": "archimedius_settings.json",
    "log_file": "archimedius.log",
}