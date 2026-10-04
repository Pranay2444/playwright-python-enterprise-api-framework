from typing import Any

from playwright.sync_api import APIResponse

from api_framework.core.api_client import ApiClient


class CartsClient:
    def __init__(self, api: ApiClient) -> None:
        self.api = api

    def list(self, *, limit: int = 10) -> APIResponse:
        return self.api.get("/carts", params={"limit": limit})

    def for_user(self, user_id: int) -> APIResponse:
        return self.api.get(f"/carts/user/{user_id}")

    def add(self, payload: dict[str, Any]) -> APIResponse:
        # DummyJSON returns a simulated creation response; it does not persist the cart.
        return self.api.post("/carts/add", data=payload)
