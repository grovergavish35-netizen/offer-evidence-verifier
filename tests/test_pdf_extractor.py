
from io import BytesIO

import pytest
from reportlab.pdfgen import canvas

from core.pdf_extractor import extract_pdf_text

def make_pdf(text):
    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)
    pdf.drawString(50, 750, text)
    pdf.save()

    return buffer.getvalue()

def test_extract_text_from_pdf():
    pdf_bytes = make_pdf("Company: ABC Technologies")

    extracted = extract_pdf_text(pdf_bytes)

    assert "ABC Technologies" in extracted

def test_reject_empty_file():
    with pytest.raises(ValueError, match="empty"):
        extract_pdf_text(b"")

def test_reject_non_pdf():
    with pytest.raises(ValueError, match="not a valid PDF"):
        extract_pdf_text(b"Hello world")

def test_reject_oversized_pdf():
    oversized = b"%PDF-" + b"x" * (5 * 1024 * 1024)

    with pytest.raises(ValueError, match="5 MB"):
        extract_pdf_text(oversized)