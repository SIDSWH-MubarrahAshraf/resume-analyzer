import os
from pypdf import PdfReader
import docx

def extract_text_from_pdf(file_path: str) -> str:
    """Extracts all text content from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"Failed to read PDF file: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Extracts all text content from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = []
        for para in doc.paragraphs:
            text.append(para.text)
        return "\n".join(text).strip()
    except Exception as e:
        raise Exception(f"Failed to read DOCX file: {str(e)}")

def extract_text(file_path: str) -> str:
    """Detects file extension and extracts text accordingly."""
    _, ext = os.path.splitext(file_path.lower())
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF and DOCX files are allowed.")
