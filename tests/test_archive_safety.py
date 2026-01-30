import io
import zipfile
from pathlib import Path

import pytest

from ingestion.archive import ArchiveExtractionError, extract_archive
from common.config import settings


def test_zip_slip_protection(tmp_path: Path):
    zip_path = tmp_path / "evil.zip"
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.writestr("../evil.txt", "bad")

    with pytest.raises(ArchiveExtractionError):
        list(extract_archive(zip_path, tmp_path / "out"))


def test_archive_size_limit(tmp_path: Path, monkeypatch):
    zip_path = tmp_path / "big.zip"
    monkeypatch.setattr(settings, "max_archive_bytes", 5)
    with zipfile.ZipFile(zip_path, "w") as zipf:
        zipf.writestr("file.txt", "1234567890")

    with pytest.raises(ArchiveExtractionError):
        list(extract_archive(zip_path, tmp_path / "out"))
