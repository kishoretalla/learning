import pytest

from backend import pdf_extractor


VALID_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n"
    b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font "
    b"/Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
    b"4 0 obj\n<< /Length 44 >>\nstream\n"
    b"BT /F1 12 Tf 100 700 Td (Hello World) Tj ET\n"
    b"endstream\nendobj\n"
    b"xref\n0 5\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000274 00000 n \n"
    b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n370\n%%EOF"
)


@pytest.mark.unit
def test_extract_with_pdfplumber_returns_page_metadata():
    pages = pdf_extractor.extract_with_pdfplumber(VALID_PDF)

    assert len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["char_count"] == len(pages[0]["text"])


@pytest.mark.unit
def test_extract_with_pypdf_normalizes_missing_text(monkeypatch):
    class FakePage:
        @staticmethod
        def extract_text():
            return None

    class FakeReader:
        def __init__(self, _stream):
            self.pages = [FakePage()]

    monkeypatch.setattr(pdf_extractor.pypdf, "PdfReader", FakeReader)

    pages = pdf_extractor.extract_with_pypdf(b"fake-pdf")

    assert pages == [{"page_number": 1, "text": "", "char_count": 0}]


@pytest.mark.unit
def test_extract_pdf_pages_falls_back_to_pypdf(monkeypatch):
    monkeypatch.setattr(pdf_extractor, "extract_with_pdfplumber", lambda _data: (_ for _ in ()).throw(RuntimeError("pdfplumber failed")))
    monkeypatch.setattr(pdf_extractor, "extract_with_pypdf", lambda _data: [{"page_number": 1, "text": "fallback", "char_count": 8}])

    pages = pdf_extractor.extract_pdf_pages(b"fake-pdf")

    assert pages[0]["text"] == "fallback"


@pytest.mark.unit
def test_extract_pdf_pages_raises_value_error_when_all_extractors_fail(monkeypatch):
    monkeypatch.setattr(pdf_extractor, "extract_with_pdfplumber", lambda _data: (_ for _ in ()).throw(RuntimeError("pdfplumber failed")))
    monkeypatch.setattr(pdf_extractor, "extract_with_pypdf", lambda _data: (_ for _ in ()).throw(RuntimeError("pypdf failed")))

    with pytest.raises(ValueError, match="Could not extract text from PDF"):
        pdf_extractor.extract_pdf_pages(b"not-a-pdf")