"""Ensure project root is importable during test collection."""

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
root_str = str(ROOT)
if root_str not in sys.path:
    sys.path.insert(0, root_str)


def write_minimal_epub(epub_path: Path) -> None:
    """Write a minimal valid EPUB zip for metadata extraction tests."""
    container_xml = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    content_opf = """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Sample Book</dc:title>
    <dc:creator>Jane Author</dc:creator>
    <dc:date>2022-01-01</dc:date>
    <dc:publisher>Test Press</dc:publisher>
    <dc:language>en</dc:language>
  </metadata>
</package>"""

    with zipfile.ZipFile(epub_path, "w") as epub:
        epub.writestr("META-INF/container.xml", container_xml)
        epub.writestr("content.opf", content_opf)
