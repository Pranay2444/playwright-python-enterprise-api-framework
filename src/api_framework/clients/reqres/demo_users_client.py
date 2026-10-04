from typing import Any

from playwright.sync_api import APIResponse

from api_framework.core.api_client import ApiClient


class DemoUsersClient:
    """Fixture users and simulated writes; no project key or persistence claim."""

    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def list(self, *, page: int = 1, per_page: int = 2) -> APIResponse:
        return self.api.get("/api/users", params={"page": page, "per_page": per_page})

    def get(self, user_id: int) -> APIResponse:
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("Demo user ID must be a positive integer")
        return self.api.get(f"/api/users/{user_id}")

    def create(self, payload: dict[str, Any]) -> APIResponse:
        return self.api.post("/api/users", data=payload)
