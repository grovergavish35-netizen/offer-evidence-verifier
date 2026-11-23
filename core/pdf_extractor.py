from io import BytesIO

import pdfplumber


MAX_PDF_SIZE = 5 * 1024 * 1024
MAX_PAGES = 15
MAX_TEXT_LENGTH = 20000


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract selectable text from a PDF."""

    if not file_bytes:
        raise ValueError("The uploaded PDF is empty.")

    if len(file_bytes) > MAX_PDF_SIZE:
        raise ValueError("PDF must be 5 MB or smaller.")

    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError("The uploaded file is not a valid PDF.")

    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            if len(pdf.pages) > MAX_PAGES:
                raise ValueError(
                    f"PDF must contain at most {MAX_PAGES} pages."
                )

            pages = []

            for page in pdf.pages:
                pages.append(page.extract_text() or "")

            full_text = "\n".join(pages).strip()

    except ValueError:
        raise

    except Exception as exc:
        raise ValueError(
            "Unable to read this PDF. It may be "
            "corrupted, encrypted, or unsupported."
        ) from exc

    if not full_text:
        raise ValueError(
            "No selectable text found. "
            "Scanned PDFs are not supported yet."
        )

    if len(full_text) > MAX_TEXT_LENGTH:
        raise ValueError(
            "Extracted text exceeds 20,000 characters."
        )

    return full_text