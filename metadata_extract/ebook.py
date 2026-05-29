"""Ebook metadata extraction."""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

from defusedxml import ElementTree as ET

logger = logging.getLogger("MediaOrganizer")


def extract_ebook_metadata(file_path: Path, metadata: dict) -> None:
    """Extract metadata from ebook files."""
    metadata.update(
        {
            "title": file_path.stem,
            "author": "Unknown",
            "year": "Unknown",
            "genre": "Unknown",
            "publisher": "Unknown",
            "isbn": "Unknown",
            "language": "Unknown",
        }
    )

    ext = file_path.suffix.lower()

    try:
        if ext == ".pdf":
            _extract_pdf_metadata(file_path, metadata)
        elif ext == ".epub":
            _extract_epub_metadata(file_path, metadata)
        elif ext in [".mobi", ".azw", ".azw3"]:
            _extract_mobi_metadata(file_path, metadata)
    except Exception as exc:
        logger.error("Error in ebook metadata extraction for %s: %s", file_path, exc)


def _extract_pdf_metadata(file_path: Path, metadata: dict) -> None:
    try:
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        info = reader.metadata
        if info:
            if info.get("/Title"):
                metadata["title"] = info["/Title"]
            if info.get("/Author"):
                metadata["author"] = info["/Author"]
            if info.get("/Producer"):
                metadata["publisher"] = info["/Producer"]
            if info.get("/CreationDate"):
                date_str = info["/CreationDate"]
                year_match = re.search(r"D:(\d{4})", date_str)
                if year_match:
                    metadata["year"] = year_match.group(1)
    except ImportError:
        logger.warning("PyPDF not available. Limited PDF metadata extraction.")
    except Exception as exc:
        logger.error("Error extracting PDF metadata from %s: %s", file_path, exc)


def _extract_epub_metadata(file_path: Path, metadata: dict) -> None:
    try:
        with zipfile.ZipFile(file_path) as epub:
            for name in epub.namelist():
                if name.endswith(".opf"):
                    with epub.open(name) as opf:
                        tree = ET.parse(opf)
                        root = tree.getroot()

                        ns = {
                            "dc": "http://purl.org/dc/elements/1.1/",
                            "opf": "http://www.idpf.org/2007/opf",
                        }

                        opf_metadata = root.find(".//{http://www.idpf.org/2007/opf}metadata")
                        if opf_metadata is not None:
                            title = opf_metadata.find(".//dc:title", ns)
                            if title is not None and title.text:
                                metadata["title"] = title.text

                            creator = opf_metadata.find(".//dc:creator", ns)
                            if creator is not None and creator.text:
                                metadata["author"] = creator.text

                            date = opf_metadata.find(".//dc:date", ns)
                            if date is not None and date.text:
                                year_match = re.search(r"\d{4}", date.text)
                                if year_match:
                                    metadata["year"] = year_match.group(0)

                            publisher = opf_metadata.find(".//dc:publisher", ns)
                            if publisher is not None and publisher.text:
                                metadata["publisher"] = publisher.text

                            language = opf_metadata.find(".//dc:language", ns)
                            if language is not None and language.text:
                                metadata["language"] = language.text

                            identifier = opf_metadata.find(".//dc:identifier", ns)
                            if identifier is not None and identifier.text:
                                scheme = identifier.get(
                                    "{http://www.idpf.org/2007/opf}scheme", ""
                                ).lower()
                                if "isbn" in scheme or re.search(
                                    r"isbn", identifier.text, re.I
                                ):
                                    metadata["isbn"] = identifier.text
                    break
    except Exception as exc:
        logger.error("Error extracting EPUB metadata from %s: %s", file_path, exc)


def _extract_mobi_metadata(file_path: Path, metadata: dict) -> None:
    try:
        import mobi

        book = mobi.Mobi(file_path)
        book.parse()

        if book.title:
            metadata["title"] = book.title
        if book.author:
            metadata["author"] = book.author
        if book.publisher:
            metadata["publisher"] = book.publisher

        if hasattr(book, "publication_date") and book.publication_date:
            year_match = re.search(r"\d{4}", book.publication_date)
            if year_match:
                metadata["year"] = year_match.group(0)

    except ImportError:
        logger.warning("mobi-python not available. Limited MOBI metadata extraction.")
    except Exception as exc:
        logger.error("Error extracting MOBI metadata from %s: %s", file_path, exc)
