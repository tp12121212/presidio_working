from pathlib import Path


def detect_type(path: Path) -> str:
    """Detect file type based on suffix."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".docx"}:
        return "docx"
    if suffix in {".pptx"}:
        return "pptx"
    if suffix in {".xlsx"}:
        return "xlsx"
    if suffix in {".txt", ".md", ".csv"}:
        return "text"
    if suffix in {".zip", ".rar", ".7z"}:
        return "archive"
    if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".gif", ".bmp"}:
        return "image"
    return "unknown"
