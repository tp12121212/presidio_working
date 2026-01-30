from __future__ import annotations

import logging
from dataclasses import dataclass
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from pathlib import Path
from typing import Iterable, List, Tuple

from bs4 import BeautifulSoup

from common.config import settings
from common.utils import safe_filename

logger = logging.getLogger(__name__)


@dataclass
class EmailExtractedItem:
    path: Path
    virtual_path: str
    warnings: list[str]


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n")


def _write_text_file(destination: Path, name: str, content: str) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    target = destination / name
    target.write_text(content, encoding="utf-8", errors="ignore")
    return target


def extract_eml(
    path: Path,
    destination: Path,
    include_headers: bool = True,
    parse_html: bool = True,
) -> Tuple[List[EmailExtractedItem], list[str]]:
    warnings: list[str] = []
    extracted: list[EmailExtractedItem] = []
    total_bytes = 0

    with path.open("rb") as handle:
        message: EmailMessage = BytesParser(policy=policy.default).parse(handle)

    header_text = ""
    if include_headers:
        header_text = "\n".join(
            f"{key}: {value}" for key, value in message.items() if value
        )

    body_text = ""
    html_text = ""
    for part in message.walk():
        content_type = part.get_content_type()
        if content_type == "text/plain" and not body_text:
            body_text = part.get_content()
        if content_type == "text/html" and not html_text:
            html_text = part.get_content()

    if not body_text and html_text and parse_html:
        body_text = _html_to_text(html_text)

    if body_text or header_text:
        combined = "\n".join([header_text, body_text]).strip()
        if combined:
            body_path = _write_text_file(destination, "body.txt", combined)
            extracted.append(
                EmailExtractedItem(
                    path=body_path,
                    virtual_path="body.txt",
                    warnings=[],
                )
            )

    if html_text and parse_html:
        html_path = _write_text_file(
            destination, "body.html.txt", _html_to_text(html_text)
        )
        extracted.append(
            EmailExtractedItem(
                path=html_path,
                virtual_path="body.html.txt",
                warnings=[],
            )
        )

    attachment_count = 0
    for part in message.iter_attachments():
        attachment_count += 1
        if attachment_count > settings.max_email_attachments:
            warnings.append("Email contains too many attachments; extra attachments skipped.")
            break
        filename = part.get_filename() or "attachment"
        safe_name = safe_filename(filename)
        payload = part.get_payload(decode=True)
        if payload is None:
            continue
        total_bytes += len(payload)
        if total_bytes > settings.max_email_bytes:
            warnings.append("Email attachments exceed size limit; extra attachments skipped.")
            break
        attachment_dir = destination / "attachments"
        attachment_dir.mkdir(parents=True, exist_ok=True)
        attachment_path = attachment_dir / safe_name
        attachment_path.write_bytes(payload)
        extracted.append(
            EmailExtractedItem(
                path=attachment_path,
                virtual_path=f"attachments/{safe_name}",
                warnings=[],
            )
        )

    for part in message.walk():
        if part.get_content_maintype() == "image":
            disposition = part.get_content_disposition()
            content_id = part.get("Content-ID")
            if disposition != "inline" and not content_id:
                continue
            filename = part.get_filename() or f"inline_{content_id or 'image'}"
            safe_name = safe_filename(filename)
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            total_bytes += len(payload)
            if total_bytes > settings.max_email_bytes:
                warnings.append("Email inline images exceed size limit; extra images skipped.")
                break
            inline_dir = destination / "inline"
            inline_dir.mkdir(parents=True, exist_ok=True)
            inline_path = inline_dir / safe_name
            inline_path.write_bytes(payload)
            extracted.append(
                EmailExtractedItem(
                    path=inline_path,
                    virtual_path=f"inline/{safe_name}",
                    warnings=[],
                )
            )

    return extracted, warnings


def extract_msg(
    path: Path,
    destination: Path,
    include_headers: bool = True,
    parse_html: bool = True,
) -> Tuple[List[EmailExtractedItem], list[str]]:
    try:
        import extract_msg  # type: ignore
    except ImportError as exc:  # pragma: no cover - dependency missing
        raise RuntimeError("extract-msg is required to parse .msg files") from exc

    warnings: list[str] = []
    extracted: list[EmailExtractedItem] = []
    total_bytes = 0

    msg = extract_msg.Message(str(path))
    msg.extract_attachments = True
    msg.save_attachments = False
    msg.process()

    header_text = ""
    if include_headers:
        header_text = "\n".join(
            [
                f"Subject: {msg.subject}" if msg.subject else "",
                f"From: {msg.sender}" if msg.sender else "",
                f"To: {msg.to}" if msg.to else "",
                f"Cc: {msg.cc}" if msg.cc else "",
                f"Date: {msg.date}" if msg.date else "",
            ]
        ).strip()

    body_text = msg.body or ""
    html_text = msg.htmlBody or ""

    if not body_text and html_text and parse_html:
        body_text = _html_to_text(html_text)

    combined = "\n".join([header_text, body_text]).strip()
    if combined:
        body_path = _write_text_file(destination, "body.txt", combined)
        extracted.append(
            EmailExtractedItem(
                path=body_path,
                virtual_path="body.txt",
                warnings=[],
            )
        )

    if html_text and parse_html:
        html_path = _write_text_file(
            destination, "body.html.txt", _html_to_text(html_text)
        )
        extracted.append(
            EmailExtractedItem(
                path=html_path,
                virtual_path="body.html.txt",
                warnings=[],
            )
        )

    attachment_dir = destination / "attachments"
    attachment_dir.mkdir(parents=True, exist_ok=True)
    attachment_count = 0
    for attachment in msg.attachments:
        attachment_count += 1
        if attachment_count > settings.max_email_attachments:
            warnings.append("Email contains too many attachments; extra attachments skipped.")
            break
        safe_name = safe_filename(attachment.longFilename or attachment.shortFilename or "attachment")
        payload = attachment.data
        if payload is None:
            continue
        total_bytes += len(payload)
        if total_bytes > settings.max_email_bytes:
            warnings.append("Email attachments exceed size limit; extra attachments skipped.")
            break
        attachment_path = attachment_dir / safe_name
        attachment_path.write_bytes(payload)
        extracted.append(
            EmailExtractedItem(
                path=attachment_path,
                virtual_path=f"attachments/{safe_name}",
                warnings=[],
            )
        )

    msg.close()
    return extracted, warnings
