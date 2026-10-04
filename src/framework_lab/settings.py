"""Explicit lab configuration; secrets never appear in repr or connection logs."""

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class LabSettings:
    database_url: str = field(repr=False)
    signing_key: str = field(repr=False)
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    access_seconds: int = 120
    refresh_seconds: int = 900
    challenge_seconds: int = 120
    max_otp_attempts: int = 3
    upload_limit: int = 65536
    issuer: str = "portfolio-lab"
    audience: str = "portfolio-api"

    def __post_init__(self) -> None:
        if len(self.signing_key.encode()) < 32:
            raise ValueError("LAB_SIGNING_KEY must contain at least 32 bytes")
        if not self.database_url.startswith(("sqlite://", "postgresql+psycopg://")):
            raise ValueError("Use SQLite or PostgreSQL with psycopg for the owned lab")
        for value in (
            self.smtp_port,
            self.access_seconds,
            self.refresh_seconds,
            self.challenge_seconds,
            self.max_otp_attempts,
            self.upload_limit,
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError("Lab limits must be positive integers")
        if self.refresh_seconds <= self.access_seconds:
            raise ValueError("Refresh lifetime must exceed access lifetime")

    @classmethod
    def from_env(cls) -> "LabSettings":
        try:
            signing_key = os.getenv("LAB_SIGNING_KEY", "")
            if not signing_key and os.getenv("LAB_SIGNING_KEY_FILE"):
                signing_key = Path(os.environ["LAB_SIGNING_KEY_FILE"]).read_text().strip()
            return cls(
                database_url=os.environ["LAB_DATABASE_URL"],
                signing_key=signing_key,
                smtp_host=os.getenv("LAB_SMTP_HOST", "127.0.0.1"),
                smtp_port=int(os.getenv("LAB_SMTP_PORT", "1025")),
            )
        except (KeyError, ValueError, OSError):
            raise ValueError(
                "Set valid LAB_DATABASE_URL, LAB_SIGNING_KEY, and SMTP settings"
            ) from None
