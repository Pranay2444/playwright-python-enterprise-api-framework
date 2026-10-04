"""DummyJSON endpoint knowledge, including its requested token duration."""

from playwright.sync_api import APIResponse

from api_framework.auth.token_manager import TokenPair
from api_framework.config import Settings
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_object


class AuthClient:
    def __init__(self, api: ApiClient, settings: Settings) -> None:
        self.api = api
        self.settings = settings

    def login(self, username: str, password: str) -> APIResponse:
        return self.api.post(
            "/auth/login",
            data={
                "username": username,
                "password": password,
                "expiresInMins": self.settings.token_expires_in_mins,
            },
        )

    def me(self, access_token: str) -> APIResponse:
        return self.api.request(
            "GET", "/auth/me", headers={"Authorization": f"Bearer {access_token}"}
        )

    def refresh(self, refresh_token: str) -> APIResponse:
        return self.api.post(
            "/auth/refresh",
            data={
                "refreshToken": refresh_token,
                "expiresInMins": self.settings.token_expires_in_mins,
            },
        )

    def obtain_tokens(self) -> TokenPair:
        return self._token_pair(self.login(self.settings.username, self.settings.password))

    def renew_tokens(self, refresh_token: str) -> TokenPair:
        return self._token_pair(self.refresh(refresh_token))

    def _token_pair(self, response: APIResponse) -> TokenPair:
        body = json_object(response)
        access = body.get("accessToken")
        refresh = body.get("refreshToken")
        if not isinstance(access, str) or not isinstance(refresh, str) or not access or not refresh:
            raise AssertionError("Auth response must include non-empty string tokens")
        # DummyJSON uses the expiresInMins we request. This is a scheduling hint,
        # not JWT signature/expiry validation; the server remains authoritative.
        return TokenPair(access, refresh, self.settings.token_expires_in_mins * 60)
