import re
from dataclasses import dataclass, field

from playwright.sync_api import APIResponse

from api_framework.config import BookerSettings
from api_framework.contracts.validation import contract_json
from api_framework.core.api_client import ApiClient


@dataclass(frozen=True)
class BookerSession:
    token: str = field(repr=False)

    def __post_init__(self) -> None:
        # Prevent a malformed token from injecting a second cookie or header.
        if not isinstance(self.token, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", self.token):
            raise ValueError("Booker token must be a nonempty cookie-safe string")

    def headers(self) -> dict[str, str]:
        return {"Cookie": f"token={self.token}"}


class BookerAuthClient:
    def __init__(self, api: ApiClient, settings: BookerSettings) -> None:
        self.api = api
        self.settings = settings

    def login(self, username: str, password: str) -> APIResponse:
        return self.api.post("/auth", data={"username": username, "password": password})

    def session(self) -> BookerSession:
        body = contract_json(
            self.login(self.settings.username, self.settings.password),
            "token",
            service="restful_booker",
        )
        return BookerSession(body["token"])
