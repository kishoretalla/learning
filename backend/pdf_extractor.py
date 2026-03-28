import io
from typing import Any

import pdfplumber
import pypdf


def extract_with_pdfplumber(data: bytes) -> list[dict[str, Any]]:
    pages = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            pages.append({"page_number": i, "text": text, "char_count": len(text)})
    return pages


def extract_with_pypdf(data: bytes) -> list[dict[str, Any]]:
    pages = []
    reader = pypdf.PdfReader(io.BytesIO(data))
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        pages.append({"page_number": i, "text": text, "char_count": len(text)})
    return pages


def extract_pdf_pages(data: bytes) -> list[dict[str, Any]]:
    try:
        return extract_with_pdfplumber(data)
    except Exception:
        try:
            return extract_with_pypdf(data)
        except Exception as exc:
            raise ValueError(f"Could not extract text from PDF: {exc}") from exc