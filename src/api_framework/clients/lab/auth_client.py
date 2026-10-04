from playwright.sync_api import APIResponse

from api_framework.core.api_client import ApiClient


class LabAuthClient:
    def __init__(self, api: ApiClient):
        self.api = api

    def register(self, email: str, password: str, mfa_method: str = "email") -> APIResponse:
        return self.api.post(
            "/auth/register", data={"email": email, "password": password, "mfa_method": mfa_method}
        )

    def login(self, email: str, password: str) -> APIResponse:
        return self.api.post("/auth/login", data={"email": email, "password": password})

    def verify(self, challenge_id: str, code: str) -> APIResponse:
        return self.api.post("/auth/verify", data={"challenge_id": challenge_id, "code": code})

    def refresh(self, refresh_token: str) -> APIResponse:
        return self.api.post("/auth/refresh", data={"refresh_token": refresh_token})

    def me(self, headers: dict[str, str] | None = None) -> APIResponse:
        return self.api.request("GET", "/auth/me", headers=headers)

    def logout(self, headers: dict[str, str]) -> APIResponse:
        return self.api.request("POST", "/auth/logout", headers=headers)
