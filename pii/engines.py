from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_image_redactor import ImageAnalyzerEngine


class PIIEngines:
    """Wrapper around Presidio engines for text and image analysis."""

    def __init__(self) -> None:
        self.text_engine = AnalyzerEngine()
        self.image_engine = ImageAnalyzerEngine(analyzer_engine=self.text_engine)

    def analyze_text(
        self, text: str, entities: List[str] | None = None, language: str = "en"
    ) -> List[RecognizerResult]:
        return self.text_engine.analyze(text=text, language=language, entities=entities)

    def analyze_image(self, path: Path) -> Tuple[str, List[RecognizerResult]]:
        ocr_result = self.image_engine.ocr.perform_ocr(str(path))
        text = self.image_engine.ocr.get_text_from_ocr_dict(ocr_result)
        results = self.text_engine.analyze(text=text, language="en")
        return text, results
