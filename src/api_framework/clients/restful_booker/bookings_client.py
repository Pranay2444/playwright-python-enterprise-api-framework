from typing import Any

from playwright.sync_api import APIResponse

from api_framework.clients.restful_booker.auth_client import BookerSession
from api_framework.core.api_client import ApiClient


class BookingsClient:
    def __init__(self, api: ApiClient, session: BookerSession | None = None) -> None:
        self.api = api
        self.session = session

    def list(self, *, firstname: str, lastname: str) -> APIResponse:
        # Require a filter so portfolio tests do not enumerate the shared dataset.
        return self.api.get("/booking", params={"firstname": firstname, "lastname": lastname})

    def get(self, booking_id: int) -> APIResponse:
        return self.api.get(f"/booking/{booking_id}")

    def create(self, payload: dict[str, Any]) -> APIResponse:
        return self.api.post("/booking", data=payload)

    def update(self, booking_id: int, payload: dict[str, Any]) -> APIResponse:
        return self._write("PUT", booking_id, payload)

    def patch(self, booking_id: int, payload: dict[str, Any]) -> APIResponse:
        return self._write("PATCH", booking_id, payload)

    def delete(self, booking_id: int) -> APIResponse:
        return self._write("DELETE", booking_id)

    def _write(
        self, method: str, booking_id: int, payload: dict[str, Any] | None = None
    ) -> APIResponse:
        headers = self.session.headers() if self.session is not None else {}
        return self.api.request(method, f"/booking/{booking_id}", data=payload, headers=headers)
