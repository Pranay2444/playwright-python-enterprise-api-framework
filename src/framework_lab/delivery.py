"""Delivery seams: real SMTP for Mailpit, explicit synthetic SMS/in-memory test adapters."""

import smtplib
from email.message import EmailMessage
from threading import Lock
from typing import Protocol


class OtpDelivery(Protocol):
    def send(self, recipient: str, challenge_id: str, code: str) -> None: ...


class SmtpDelivery:
    def __init__(self, host: str, port: int):
        self.host, self.port = host, port

    def send(self, recipient: str, challenge_id: str, code: str) -> None:
        message = EmailMessage()
        message["From"] = "otp@portfolio.example.test"
        message["To"] = recipient
        message["Subject"] = f"Lab sign-in {challenge_id}"
        message.set_content(f"Challenge: {challenge_id}\nCode: {code}\n")
        with smtplib.SMTP(self.host, self.port, timeout=5) as smtp:
            smtp.send_message(message)


class CapturedDelivery:
    """A test-owned delivery adapter; never exposed through an application endpoint."""

    def __init__(self):
        self.messages: dict[tuple[str, str], str] = {}
        self.lock = Lock()

    def send(self, recipient: str, challenge_id: str, code: str) -> None:
        with self.lock:
            self.messages[recipient, challenge_id] = code

    def code_for(self, recipient: str, challenge_id: str) -> str:
        with self.lock:
            return self.messages[recipient, challenge_id]
