from collections.abc import Iterator

import pytest
from playwright.sync_api import Error, Playwright

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.dummyjson.auth_client import AuthClient
from api_framework.config import Settings
from api_framework.core.api_client import ApiClient, ApiTransportError
from api_framework.core.responses import json_object
from tests.support.local_api import LocalApi


@pytest.fixture
def local_client(playwright: Playwright, local_api: LocalApi) -> Iterator[ApiClient]:
    context = playwright.request.new_context(base_url=local_api.base_url, timeout=1000)
    yield ApiClient(context)
    context.dispose()


def test_http_error_is_returned_once(local_client: ApiClient, local_api: LocalApi) -> None:
    response = local_client.get("/unavailable")
    assert response.status == 503
    assert local_api.requests == [("GET", "/unavailable")]
    with pytest.raises(AssertionError, match="Expected HTTP 200; received HTTP 503"):
        json_object(response)


def test_query_values_are_encoded_and_omitted_from_logs(
    local_client: ApiClient, caplog: pytest.LogCaptureFixture
) -> None:
    query = "Demo Hammer & private=value"
    result = json_object(local_client.get("/products/search", params={"q": query}))
    assert result["products"] == []
    assert query not in caplog.text
    assert "GET /products/search -> 200" in caplog.text


@pytest.mark.parametrize(
    "path",
    [
        "https://other.example/products",
        "//other.example/products",
        "products",
        "/products?q=secret",
        "/products#fragment",
        "/\\other.example/products",
    ],
)
def test_reject_urls_that_could_bypass_origin_or_expose_query(
    local_client: ApiClient, local_api: LocalApi, path: str
) -> None:
    with pytest.raises(ValueError, match="origin-relative"):
        local_client.get(path)
    assert local_api.requests == []


def test_login_cookies_do_not_authenticate_separate_context(
    local_client: ApiClient, playwright: Playwright, local_api: LocalApi
) -> None:
    settings = Settings(base_url=local_api.base_url, username="demo-user", password="demo-password")
    login_context = playwright.request.new_context(base_url=local_api.base_url)
    try:
        source = AuthClient(ApiClient(login_context), settings)
        manager = TokenManager(source)
        authenticated = ApiClient(local_client.context, manager)
        assert json_object(authenticated.get("/auth/me"))["username"] == settings.username
        assert local_client.get("/auth/me").status == 401
        assert local_api.login_count == 1
    finally:
        login_context.dispose()


def test_transport_error_does_not_echo_playwright_call_log(
    local_client: ApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failed_fetch(*args: object, **kwargs: object) -> None:
        raise Error("Call log: Authorization: Bearer private-token")

    monkeypatch.setattr(local_client.context, "fetch", failed_fetch)
    with pytest.raises(ApiTransportError) as error:
        local_client.get("/auth/me")
    assert "private-token" not in str(error.value)


def test_token_refresh_reaches_http_endpoint(local_client: ApiClient, local_api: LocalApi) -> None:
    settings = Settings(base_url=local_api.base_url, username="demo-user", password="demo-password")
    now = [0.0]
    manager = TokenManager(AuthClient(local_client, settings), clock=lambda: now[0])
    assert (
        json_object(
            local_client.request(
                "GET",
                "/auth/me",
                headers={
                    "Authorization": manager.authorization_header(),
                },
            )
        )["id"]
        == local_api.user["id"]
    )
    now[0] = 270.0
    assert (
        json_object(
            local_client.request(
                "GET",
                "/auth/me",
                headers={
                    "Authorization": manager.authorization_header(),
                },
            )
        )["id"]
        == local_api.user["id"]
    )
    assert local_api.login_count == 1
    assert local_api.refresh_count == 1
