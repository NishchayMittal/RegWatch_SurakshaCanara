"""
Email Parser — Person A (Week 1 skeleton, Week 2 full implementation)
Monitors a dedicated mailbox for circulars forwarded by compliance team.

Week 1: IMAP connection + subject filter + text extraction skeleton
Week 2: PDF attachment parsing, HTML email cleanup, threading support
"""

import email
import imaplib
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from email.header import decode_header
from typing import Optional

from app.agents.watcher_real import CircularDoc

logger = logging.getLogger(__name__)


@dataclass
class EmailConfig:
    host: str
    port: int
    username: str
    password: str
    folder: str = "INBOX"
    # Only process emails from these senders (whitelist)
    trusted_senders: list[str] = None

    def __post_init__(self):
        if self.trusted_senders is None:
            # RBI, SEBI, MCA official domains + internal compliance forwarder
            self.trusted_senders = [
                "rbi.org.in",
                "sebi.gov.in",
                "mca.gov.in",
                "compliance@yourbank.com",   # internal forwarder
            ]


class EmailParser:
    """
    IMAP-based email monitor. Checks mailbox, extracts circular content,
    returns CircularDoc objects identical to WatcherAgent output.

    Usage (called by orchestrator on schedule):
        parser = EmailParser(config)
        docs = parser.fetch_new_circulars()
    """

    # Keywords in subject line that suggest a regulatory circular
    CIRCULAR_KEYWORDS = [
        "circular", "notification", "directive", "master direction",
        "rbi", "sebi", "mca", "compliance", "regulation", "amendment",
    ]

    def __init__(self, config: EmailConfig):
        self.config = config
        self._conn: Optional[imaplib.IMAP4_SSL] = None

    # ── Public API ───────────────────────────────────────────────────────────

    def fetch_new_circulars(self) -> list[CircularDoc]:
        """Connect, fetch unseen relevant emails, disconnect, return docs."""
        docs = []
        try:
            self._connect()
            raw_emails = self._fetch_unseen()
            for raw in raw_emails:
                doc = self._parse_email(raw)
                if doc:
                    docs.append(doc)
            logger.info(f"EmailParser extracted {len(docs)} circulars from email")
        except Exception as e:
            logger.error(f"EmailParser failed: {e}")
        finally:
            self._disconnect()
        return docs

    # ── IMAP connection ──────────────────────────────────────────────────────

    def _connect(self):
        self._conn = imaplib.IMAP4_SSL(self.config.host, self.config.port)
        self._conn.login(self.config.username, self.config.password)
        self._conn.select(self.config.folder)
        logger.debug(f"IMAP connected: {self.config.host}")

    def _disconnect(self):
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def _fetch_unseen(self) -> list[bytes]:
        """Fetch all UNSEEN emails — marks them seen after fetch."""
        _, data = self._conn.search(None, "UNSEEN")
        email_ids = data[0].split()

        raw_emails = []
        for eid in email_ids:
            _, msg_data = self._conn.fetch(eid, "(RFC822)")
            raw_emails.append(msg_data[0][1])

        logger.debug(f"Fetched {len(raw_emails)} unseen emails")
        return raw_emails

    # ── Email parsing ────────────────────────────────────────────────────────

    def _parse_email(self, raw: bytes) -> Optional[CircularDoc]:
        """Parse raw email bytes into CircularDoc."""
        msg = email.message_from_bytes(raw)

        subject = self._decode_header(msg["Subject"])
        sender  = msg.get("From", "")
        date    = self._parse_date(msg.get("Date", ""))

        # Skip if not from trusted sender
        if not self._is_trusted_sender(sender):
            logger.debug(f"Skipping untrusted sender: {sender}")
            return None

        # Skip if subject doesn't look like a circular
        if not self._is_circular_subject(subject):
            logger.debug(f"Skipping non-circular subject: {subject}")
            return None

        regulator = self._detect_regulator(sender, subject)
        body = self._extract_body(msg)

        if not body or len(body) < 100:
            logger.debug(f"Empty body for: {subject}")
            return None

        # Use a synthetic URL (email ID as stable identifier)
        url = f"email://{sender}/{date.isoformat()}/{hash(subject)}"

        return CircularDoc(
            url=url,
            title=subject,
            regulator=regulator,
            published_at=date,
            raw_text=body,
            source="email",
        )

    def _extract_body(self, msg: email.message.Message) -> str:
        """
        Extract text from email body.
        Week 1: plain text + basic HTML stripping
        Week 2 TODO: PDF attachment parsing via pdfplumber
        """
        parts = []

        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments in Week 1 (PDF handling Week 2)
            if "attachment" in disposition:
                filename = part.get_filename() or ""
                if filename.endswith(".pdf"):
                    logger.debug(f"PDF attachment skipped (Week 2 TODO): {filename}")
                continue

            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    parts.append(payload.decode(charset, errors="replace"))
                except Exception as e:
                    logger.debug(f"Plain text decode failed: {e}")

            elif content_type == "text/html":
                try:
                    from bs4 import BeautifulSoup
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
                    soup = BeautifulSoup(html, "html.parser")
                    parts.append(soup.get_text(separator="\n", strip=True))
                except Exception as e:
                    logger.debug(f"HTML parse failed: {e}")

        return "\n\n".join(parts)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _is_trusted_sender(self, sender: str) -> bool:
        sender_lower = sender.lower()
        return any(domain in sender_lower for domain in self.config.trusted_senders)

    def _is_circular_subject(self, subject: str) -> bool:
        subject_lower = subject.lower()
        return any(kw in subject_lower for kw in self.CIRCULAR_KEYWORDS)

    def _detect_regulator(self, sender: str, subject: str) -> str:
        text = (sender + " " + subject).lower()
        if "rbi" in text or "rbi.org.in" in text:
            return "RBI"
        if "sebi" in text or "sebi.gov.in" in text:
            return "SEBI"
        if "mca" in text or "mca.gov.in" in text:
            return "MCA"
        return "UNKNOWN"

    def _decode_header(self, value: Optional[str]) -> str:
        if not value:
            return ""
        decoded_parts = decode_header(value)
        parts = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                parts.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                parts.append(part)
        return " ".join(parts)

    def _parse_date(self, date_str: str) -> datetime:
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except Exception:
            return datetime.utcnow()


# ── Config from environment (12-factor) ─────────────────────────────────────

def email_config_from_env() -> EmailConfig:
    return EmailConfig(
        host=os.environ["EMAIL_IMAP_HOST"],
        port=int(os.environ.get("EMAIL_IMAP_PORT", 993)),
        username=os.environ["EMAIL_USERNAME"],
        password=os.environ["EMAIL_PASSWORD"],
        folder=os.environ.get("EMAIL_FOLDER", "INBOX"),
    )
