"""Compose the same clients against local HTTP or the explicitly enabled live API."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from playwright.sync_api import APIRequestContext, Playwright, sync_playwright

from api_framework.auth.token_manager import TokenManager
from api_framework.clients.dummyjson.auth_client import AuthClient
from api_framework.clients.dummyjson.carts_client import CartsClient
from api_framework.clients.dummyjson.products_client import ProductsClient
from api_framework.clients.dummyjson.users_client import UsersClient
from api_framework.config import Settings
from api_framework.core.api_client import ApiClient
from tests.support.local_api import LocalApi

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-external", action="store_true", default=False, help="Enable live DummyJSON tests"
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-external"):
        return
    for item in items:
        if "external" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Live service: enable with --run-external"))


@pytest.fixture(scope="session")
def playwright() -> Iterator[Playwright]:
    # The request API uses the Playwright driver; no browser is launched or downloaded.
    with sync_playwright() as instance:
        yield instance


@pytest.fixture
def local_api() -> Iterator[LocalApi]:
    with LocalApi() as server:
        yield server


@pytest.fixture(params=["local", pytest.param("live", marks=pytest.mark.external)])
def settings(request: pytest.FixtureRequest) -> Settings:
    if request.param == "local":
        server = request.getfixturevalue("local_api")
        return Settings(base_url=server.base_url, username="demo-user", password="demo-password")
    return Settings.from_env(PROJECT_ROOT / ".env")


def create_context(playwright: Playwright, settings: Settings) -> APIRequestContext:
    return playwright.request.new_context(
        base_url=settings.base_url,
        timeout=settings.timeout_ms,
        extra_http_headers={"Accept": "application/json"},
        ignore_https_errors=False,
    )


@pytest.fixture
def api_context(playwright: Playwright, settings: Settings) -> Iterator[APIRequestContext]:
    context = create_context(playwright, settings)
    yield context
    context.dispose()


@pytest.fixture
def auth_context(playwright: Playwright, settings: Settings) -> Iterator[APIRequestContext]:
    # DummyJSON sets auth cookies: keep login cookies away from public/anonymous calls.
    context = create_context(playwright, settings)
    yield context
    context.dispose()


@pytest.fixture
def api(api_context: APIRequestContext) -> ApiClient:
    return ApiClient(api_context)


@pytest.fixture
def auth_client(auth_context: APIRequestContext, settings: Settings) -> AuthClient:
    return AuthClient(ApiClient(auth_context), settings)


@pytest.fixture
def token_manager(auth_client: AuthClient) -> TokenManager:
    return TokenManager(auth_client)


@pytest.fixture
def authenticated_api(api_context: APIRequestContext, token_manager: TokenManager) -> ApiClient:
    return ApiClient(api_context, token_manager)


@pytest.fixture
def products_client(api: ApiClient) -> ProductsClient:
    return ProductsClient(api)


@pytest.fixture
def users_client(authenticated_api: ApiClient) -> UsersClient:
    return UsersClient(authenticated_api)


@pytest.fixture
def carts_client(api: ApiClient) -> CartsClient:
    return CartsClient(api)
