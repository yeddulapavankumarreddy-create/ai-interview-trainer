"""
Resume Service
--------------
Handles file upload, text extraction (PDF / DOCX / TXT),
and delegates to Granite for structured parsing.
"""

import os
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(Path(__file__).parent.parent.parent.parent / "uploads"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def save_upload(file_content: bytes, filename: str, profile_id: int) -> str:
    """Save uploaded file and return the file path."""
    upload_path = Path(UPLOAD_DIR) / str(profile_id)
    upload_path.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    file_path = upload_path / safe_name

    with open(file_path, "wb") as f:
        f.write(file_content)
    return str(file_path)


def extract_text(file_path: str, filename: str) -> Tuple[str, str]:
    """
    Extract plain text from a resume file.
    Returns (extracted_text, error_message).
    error_message is empty string on success.
    """
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext == ".docx":
        return _extract_docx(file_path)
    elif ext == ".txt":
        try:
            text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            return text, ""
        except Exception as exc:
            return "", f"Failed to read text file: {exc}"
    else:
        return "", f"Unsupported file type: {ext}"


def _extract_pdf(file_path: str) -> Tuple[str, str]:
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts), ""
    except ImportError:
        pass

    try:
        import PyPDF2
        text_parts = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n".join(text_parts), ""
    except ImportError:
        pass

    return "", "PDF extraction library not available. Please install pdfplumber: pip install pdfplumber"


def _extract_docx(file_path: str) -> Tuple[str, str]:
    try:
        from docx import Document
        doc = Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        return text, ""
    except ImportError:
        return "", "python-docx not installed. Install with: pip install python-docx"
    except Exception as exc:
        return "", f"Failed to read DOCX: {exc}"
