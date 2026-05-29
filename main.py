#!/usr/bin/env python3
"""
Archimedius - A tool to organize media files based on metadata.
"""

import logging
from pathlib import Path

from ttkbootstrap import Window

# Import application modules
import defaults
from archimedius_gui import ArchimediusGUI
from settings import configure_logging, load_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("archimedius.log")],
)
logger = logging.getLogger("Archimedius")

# Set PyPDF logger to ERROR level to suppress warnings
logging.getLogger("pypdf").setLevel(logging.ERROR)


def main():
    """Main entry point for the application."""
    configure_logging(load_settings())

    root = Window(themename="flatly")
    app = ArchimediusGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
