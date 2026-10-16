from pathlib import Path

def extract_resume_text(file_path: str) -> str:
    """Extract text from PDF or plain-text resumes."""
    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            with fitz.open(file_path) as pdf:
                return "\n".join(page.get_text("text") for page in pdf)
        except Exception as exc:
            raise ValueError(f"Could not read PDF: {exc}") from exc
    if suffix == ".txt":
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Unsupported resume type. Upload a PDF or TXT file.")
