import io
import docx
from pypdf import PdfReader


def parse_pdf(file_bytes: bytes) -> str:
    """Parse PDF file bytes into a clean string."""
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    text_parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_parts.append(text)
    return "\n".join(text_parts)


def parse_docx(file_bytes: bytes) -> str:
    """Parse DOCX file bytes into a clean string."""
    docx_file = io.BytesIO(file_bytes)
    doc = docx.Document(docx_file)
    text_parts = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(text_parts)


def parse_txt(file_bytes: bytes) -> str:
    """Parse TXT file bytes into a clean string."""
    return file_bytes.decode("utf-8", errors="ignore")
