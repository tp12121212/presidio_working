from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import py7zr
import rarfile

from common.config import settings


class ArchiveExtractionError(Exception):
    """Raised when archive extraction fails."""


def _safe_join(base: Path, target: Path) -> Path:
    resolved = (base / target).resolve()
    if base.resolve() not in resolved.parents and resolved != base.resolve():
        raise ArchiveExtractionError("Archive entry is outside extraction dir")
    return resolved


def _extract_zip(path: Path, destination: Path) -> List[Path]:
    import zipfile

    extracted: List[Path] = []
    with zipfile.ZipFile(path) as zip_ref:
        members = zip_ref.infolist()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        for member in members:
            if member.is_dir():
                continue
            member_path = Path(member.filename)
            target = _safe_join(destination, member_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zip_ref.open(member) as source, target.open("wb") as dest:
                dest.write(source.read())
            extracted.append(target)
    return extracted


def _extract_rar(path: Path, destination: Path) -> List[Path]:
    extracted: List[Path] = []
    with rarfile.RarFile(path) as rar_ref:
        members = rar_ref.infolist()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        for member in members:
            if member.isdir():
                continue
            member_path = Path(member.filename)
            target = _safe_join(destination, member_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with rar_ref.open(member) as source, target.open("wb") as dest:
                dest.write(source.read())
            extracted.append(target)
    return extracted


def _extract_7z(path: Path, destination: Path) -> List[Path]:
    extracted: List[Path] = []
    with py7zr.SevenZipFile(path, mode="r") as archive:
        members = archive.getnames()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        archive.extractall(path=destination)
        for name in members:
            target = _safe_join(destination, Path(name))
            if target.is_file():
                extracted.append(target)
    return extracted


def extract_archive(path: Path, destination: Path) -> Iterable[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return _extract_zip(path, destination)
    if suffix == ".rar":
        return _extract_rar(path, destination)
    if suffix == ".7z":
        return _extract_7z(path, destination)
    raise ArchiveExtractionError("Unsupported archive type")
