"""A small wrapper: domain clients describe endpoints; this class sends HTTP."""

import logging
from collections.abc import Mapping
from time import perf_counter
from typing import TYPE_CHECKING, Any
from urllib.parse import urlsplit

from playwright.sync_api import APIRequestContext, APIResponse, Error

if TYPE_CHECKING:
    from api_framework.auth.token_manager import TokenManager

logger = logging.getLogger(__name__)


class ApiTransportError(RuntimeError):
    """The request failed before an HTTP response was available."""


class ApiClient:
    def __init__(
        self, context: APIRequestContext, token_manager: "TokenManager | None" = None
    ) -> None:
        self.context = context
        self.token_manager = token_manager

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, str | int | float | bool] | None = None,
        data: dict[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> APIResponse:
        endpoint = urlsplit(path)
        if (
            not path.startswith("/")
            or path.startswith("//")
            or "\\" in path
            or endpoint.scheme
            or endpoint.netloc
            or endpoint.query
            or endpoint.fragment
        ):
            raise ValueError("Use an origin-relative path and pass query values through params")

        request_headers = dict(headers or {})
        if self.token_manager is not None:
            if any(name.lower() == "authorization" for name in request_headers):
                raise ValueError("Use an unauthenticated ApiClient for an explicit auth header")
            request_headers["Authorization"] = self.token_manager.authorization_header()

        start = perf_counter()
        try:
            response = self.context.fetch(
                path,
                method=method.upper(),
                params=dict(params) if params is not None else None,
                data=data,
                headers=request_headers,
                fail_on_status_code=False,
                max_retries=0,
                max_redirects=0,
            )
        except Error:
            # Playwright's transport call log can include headers. Keep it out of reports.
            raise ApiTransportError(
                f"{method.upper()} {endpoint.path} failed before receiving an HTTP response; "
                "check connectivity, TLS, and the configured timeout"
            ) from None

        logger.info(
            "%s %s -> %s (%.0f ms)",
            method.upper(),
            endpoint.path,
            response.status,
            (perf_counter() - start) * 1000,
        )
        # Do not log query values, headers, request bodies, or response bodies.
        return response

    def get(
        self, path: str, *, params: Mapping[str, str | int | float | bool] | None = None
    ) -> APIResponse:
        return self.request("GET", path, params=params)

    def post(self, path: str, *, data: dict[str, Any]) -> APIResponse:
        return self.request("POST", path, data=data)
