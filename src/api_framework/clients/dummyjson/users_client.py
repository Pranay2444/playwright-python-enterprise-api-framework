from playwright.sync_api import APIResponse

from api_framework.core.api_client import ApiClient


class UsersClient:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def list(self, *, limit: int = 10) -> APIResponse:
        return self.api.get("/users", params={"limit": limit})

    def get(self, user_id: int) -> APIResponse:
        return self.api.get(f"/users/{user_id}")

    def me(self) -> APIResponse:
        return self.api.get("/auth/me")
