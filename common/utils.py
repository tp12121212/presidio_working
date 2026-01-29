import hashlib
import os
from pathlib import Path
from typing import Iterator


def safe_filename(filename: str) -> str:
    """Sanitize filenames to avoid traversal and unsafe characters."""

    filename = os.path.basename(filename)
    return "".join(char for char in filename if char.isalnum() or char in "._-")


def ensure_within_base(path: Path, base: Path) -> Path:
    """Ensure the resolved path is within a base directory."""

    resolved = path.resolve()
    base_resolved = base.resolve()
    if base_resolved not in resolved.parents and resolved != base_resolved:
        raise ValueError("Path is outside the allowed base directory")
    return resolved


def file_hash(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Compute SHA-256 hash for a file without loading into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stream_file_chunks(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[str]:
    """Yield decoded chunks from a text file safely."""

    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            yield chunk.decode("utf-8", errors="ignore")
