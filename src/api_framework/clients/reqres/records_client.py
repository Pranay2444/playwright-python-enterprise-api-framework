import re
from typing import Any

from playwright.sync_api import APIResponse

from api_framework.clients.reqres.api_key import ApiKeyAuth
from api_framework.config import ReqResSettings
from api_framework.core.api_client import ApiClient


def safe_record_id(record_id: str) -> bool:
    return isinstance(record_id, str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,128}", record_id))


class RecordsClient:
    def __init__(self, api: ApiClient, settings: ReqResSettings) -> None:
        settings.require_project()
        self.api = api
        self.settings = settings
        self.auth = ApiKeyAuth(settings.api_key)
        self.path = f"/api/collections/{settings.collection}/records"

    def list(self, *, search: str, limit: int = 10) -> APIResponse:
        # Tests search only their synthetic marker; no broad dataset enumeration.
        if not search:
            raise ValueError("Record list requires a search value")
        return self._request("GET", params={"search": search, "limit": limit})

    def get(self, record_id: str) -> APIResponse:
        return self._request("GET", record_id)

    def create(self, data: dict[str, Any]) -> APIResponse:
        return self._request("POST", data={"data": data})

    def update(self, record_id: str, data: dict[str, Any]) -> APIResponse:
        return self._request("PUT", record_id, data={"data": data})

    def delete(self, record_id: str) -> APIResponse:
        return self._request("DELETE", record_id)

    def _request(
        self,
        method: str,
        record_id: str | None = None,
        *,
        data: dict[str, Any] | None = None,
        params: dict[str, str | int] | None = None,
    ) -> APIResponse:
        path = self.path
        if record_id is not None:
            if not safe_record_id(record_id):
                raise ValueError("Record ID must be a safe nonempty path segment")
            path += f"/{record_id}"
        return self.api.request(
            method,
            path,
            params={**(params or {}), "project_id": self.settings.project_id},
            data=data,
            headers={**self.auth.headers(), "X-Reqres-Env": self.settings.environment},
        )
