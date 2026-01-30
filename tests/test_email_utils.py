from email.message import EmailMessage
from pathlib import Path
import sys
import types

from ingestion.email_utils import extract_eml, extract_msg


def test_extract_eml_with_attachment(tmp_path: Path):
    message = EmailMessage()
    message["Subject"] = "Hello"
    message["From"] = "sender@example.com"
    message["To"] = "receiver@example.com"
    message.set_content("Plain text body")
    message.add_attachment(b"data", maintype="application", subtype="octet-stream", filename="note.txt")

    eml_path = tmp_path / "sample.eml"
    eml_path.write_bytes(message.as_bytes())

    items, warnings = extract_eml(eml_path, tmp_path / "out", include_headers=True, parse_html=True)
    paths = [item.virtual_path for item in items]

    assert "body.txt" in paths
    assert "attachments/note.txt" in paths
    assert warnings == []


def test_extract_msg_with_mock(tmp_path: Path, monkeypatch):
    class FakeAttachment:
        def __init__(self):
            self.data = b"attachment"
            self.longFilename = "file.pdf"
            self.shortFilename = None

    class FakeMessage:
        subject = "Test"
        sender = "sender@example.com"
        to = "receiver@example.com"
        cc = ""
        date = "2026-01-30"
        body = "Body text"
        htmlBody = ""
        attachments = [FakeAttachment()]

        def __init__(self, *_args, **_kwargs):
            pass

        def process(self):
            return None

        def close(self):
            return None

    fake_module = types.SimpleNamespace(Message=FakeMessage)
    monkeypatch.setitem(sys.modules, "extract_msg", fake_module)

    msg_path = tmp_path / "sample.msg"
    msg_path.write_bytes(b"fake")

    items, warnings = extract_msg(msg_path, tmp_path / "out", include_headers=True, parse_html=True)
    paths = [item.virtual_path for item in items]

    assert "body.txt" in paths
    assert "attachments/file.pdf" in paths
    assert warnings == []
