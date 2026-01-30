from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class ExtractedItem:
    path: Path
    relative_path: str


def _enforce_size_limit(total_bytes: int) -> None:
    if total_bytes > settings.max_archive_bytes:
        raise ArchiveExtractionError("Archive exceeds max extracted bytes")


def _extract_zip(path: Path, destination: Path) -> List[ExtractedItem]:
    import zipfile

    extracted: List[ExtractedItem] = []
    total_bytes = 0
    with zipfile.ZipFile(path) as zip_ref:
        members = zip_ref.infolist()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        for member in members:
            if member.is_dir():
                continue
            total_bytes += member.file_size
            _enforce_size_limit(total_bytes)
            member_path = Path(member.filename)
            target = _safe_join(destination, member_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with zip_ref.open(member) as source, target.open("wb") as dest:
                dest.write(source.read())
            extracted.append(ExtractedItem(target, member.filename))
    return extracted


def _extract_rar(path: Path, destination: Path) -> List[ExtractedItem]:
    extracted: List[ExtractedItem] = []
    total_bytes = 0
    with rarfile.RarFile(path) as rar_ref:
        members = rar_ref.infolist()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        for member in members:
            if member.isdir():
                continue
            total_bytes += member.file_size
            _enforce_size_limit(total_bytes)
            member_path = Path(member.filename)
            target = _safe_join(destination, member_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with rar_ref.open(member) as source, target.open("wb") as dest:
                dest.write(source.read())
            extracted.append(ExtractedItem(target, member.filename))
    return extracted


def _extract_7z(path: Path, destination: Path) -> List[ExtractedItem]:
    extracted: List[ExtractedItem] = []
    with py7zr.SevenZipFile(path, mode="r") as archive:
        members = archive.list()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        total_bytes = sum(member.uncompressed or 0 for member in members)
        _enforce_size_limit(total_bytes)
        archive.extractall(path=destination)
        for member in members:
            target = _safe_join(destination, Path(member.filename))
            if target.is_file():
                extracted.append(ExtractedItem(target, member.filename))
    return extracted


def _extract_tar(path: Path, destination: Path) -> List[ExtractedItem]:
    import tarfile

    extracted: List[ExtractedItem] = []
    total_bytes = 0
    with tarfile.open(path) as tar_ref:
        members = tar_ref.getmembers()
        if len(members) > settings.max_archive_files:
            raise ArchiveExtractionError("Archive contains too many files")
        for member in members:
            if not member.isfile():
                continue
            total_bytes += member.size
            _enforce_size_limit(total_bytes)
            member_path = Path(member.name)
            target = _safe_join(destination, member_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            with tar_ref.extractfile(member) as source, target.open("wb") as dest:
                if source:
                    dest.write(source.read())
            extracted.append(ExtractedItem(target, member.name))
    return extracted


def extract_archive(path: Path, destination: Path) -> Iterable[ExtractedItem]:
    destination.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.lower()
    suffixes = [s.lower() for s in path.suffixes]
    if suffix == ".zip":
        return _extract_zip(path, destination)
    if suffix == ".rar":
        return _extract_rar(path, destination)
    if suffix == ".7z":
        return _extract_7z(path, destination)
    if suffix in {".tar", ".tgz"} or suffixes[-2:] == [".tar", ".gz"]:
        return _extract_tar(path, destination)
    raise ArchiveExtractionError("Unsupported archive type")
