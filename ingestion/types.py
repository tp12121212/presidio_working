from pathlib import Path


def detect_type(path: Path) -> str:
    """Detect file type based on suffix."""

    suffix = path.suffix.lower()
    suffixes = [s.lower() for s in path.suffixes]
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
    if suffix in {".eml", ".msg"}:
        return "email"
    if suffix in {".zip", ".rar", ".7z", ".tar", ".tgz"} or suffixes[-2:] == [
        ".tar",
        ".gz",
    ]:
        return "archive"
    if suffix in {".png", ".jpg", ".jpeg", ".tiff", ".gif", ".bmp"}:
        return "image"
    return "unknown"
