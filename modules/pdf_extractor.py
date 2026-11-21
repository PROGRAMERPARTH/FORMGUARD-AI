"""
FORMGUARD AI - PDF Extractor Module
Specialized PDF text and metadata extraction.
"""

import os
from typing import Dict, List, Optional, Tuple


def extract_pdf_text(file_path: str) -> Tuple[str, Dict]:
    """
    Extract text and metadata from a PDF file.
    Returns: (text, metadata_dict)
    """
    metadata = {
        "page_count": 0,
        "title": "",
        "author": "",
        "creation_date": "",
        "file_size": 0,
    }

    if not os.path.exists(file_path):
        return "", metadata

    metadata["file_size"] = os.path.getsize(file_path)

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(file_path)
        metadata["page_count"] = len(doc)

        # Extract metadata
        pdf_meta = doc.metadata
        if pdf_meta:
            metadata["title"] = pdf_meta.get("title", "")
            metadata["author"] = pdf_meta.get("author", "")
            metadata["creation_date"] = pdf_meta.get("creationDate", "")

        # Extract text from all pages
        pages_text = []
        for page in doc:
            page_text = page.get_text("text")
            if page_text.strip():
                pages_text.append(page_text)

        doc.close()

        full_text = "\n\n".join(pages_text)
        return full_text, metadata

    except ImportError:
        return "", metadata
    except Exception as e:
        return "", metadata


def extract_pdf_pages(file_path: str) -> List[Dict]:
    """
    Extract text from each page separately.
    Returns list of {page_number, text, has_text}
    """
    pages = []

    try:
        import fitz

        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            pages.append({
                "page_number": i + 1,
                "text": text,
                "has_text": bool(text),
            })
        doc.close()

    except (ImportError, Exception):
        pass

    return pages
