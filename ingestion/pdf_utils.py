from pathlib import Path
from typing import List

import fitz
from pdfminer.high_level import extract_text


def extract_text_pdf(path: Path) -> str:
    return extract_text(str(path))


def render_pdf_to_images(path: Path, output_dir: Path, max_pages: int) -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(path))
    image_paths: List[Path] = []
    for page_number in range(min(len(doc), max_pages)):
        page = doc.load_page(page_number)
        pix = page.get_pixmap()
        image_path = output_dir / f"page_{page_number + 1}.png"
        pix.save(str(image_path))
        image_paths.append(image_path)
    doc.close()
    return image_paths
