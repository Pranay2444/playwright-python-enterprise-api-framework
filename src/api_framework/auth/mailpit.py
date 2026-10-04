"""Bounded delivery polling; correlate recipient AND challenge, never the newest inbox OTP."""

import re
import time

from api_framework.core.responses import json_object


class MailpitCodeReader:
    def __init__(self, api, recipient: str, timeout_seconds: float = 8):
        if not 0 < timeout_seconds <= 30:
            raise ValueError("Use a positive mailbox timeout of at most 30 seconds")
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.+-]{0,90}@example\.test", recipient):
            raise ValueError("Use a synthetic example.test mailbox recipient")
        self.api, self.recipient, self.timeout = api, recipient, timeout_seconds

    def __call__(self, challenge_id: str) -> str:
        from uuid import UUID

        challenge_id = str(UUID(challenge_id))
        deadline = time.monotonic() + self.timeout
        while True:
            result = json_object(
                self.api.get(
                    "/api/v1/search",
                    params={
                        "query": f"to:{self.recipient} subject:{challenge_id}",
                    },
                )
            )
            for message in result.get("messages", []):
                if message.get("Subject") != f"Lab sign-in {challenge_id}":
                    continue
                if not any(to.get("Address") == self.recipient for to in message.get("To", [])):
                    continue
                message_id = str(UUID(message["ID"]))
                details = json_object(self.api.get(f"/api/v1/message/{message_id}"))
                text = details.get("Text", "")
                match = re.fullmatch(
                    rf"Challenge: {re.escape(challenge_id)}\nCode: ([0-9]{{6}})\n?",
                    text.strip() + "\n",
                )
                if match:
                    return match.group(1)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("Correlated OTP delivery did not arrive before the deadline")
            time.sleep(min(0.1, remaining))
