"""Independent Booker targets; no DummyJSON settings or tokens cross into this service."""

from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from api_framework.clients.restful_booker.auth_client import BookerAuthClient
from api_framework.clients.restful_booker.bookings_client import BookingsClient
from api_framework.config import BookerSettings
from api_framework.core.api_client import ApiClient
from tests.conftest import PROJECT_ROOT, create_context
from tests.support.booking_lifecycle import BookingTracker


@pytest.fixture(params=["local", pytest.param("live", marks=pytest.mark.external)])
def booker_settings(request: pytest.FixtureRequest) -> BookerSettings:
    if request.param == "local":
        server = request.getfixturevalue("local_booker")
        return BookerSettings(
            base_url=server.base_url, username="local-admin", password="local-password"
        )
    return BookerSettings.from_env(PROJECT_ROOT / ".env")


@pytest.fixture
def booker_context(
    playwright: Playwright, booker_settings: BookerSettings
) -> Iterator[APIRequestContext]:
    context = create_context(playwright, booker_settings)
    try:
        yield context
    finally:
        context.dispose()


@pytest.fixture
def booker_api(booker_context: APIRequestContext) -> ApiClient:
    return ApiClient(booker_context)


@pytest.fixture
def booker_auth(
    playwright: Playwright, booker_settings: BookerSettings
) -> Iterator[BookerAuthClient]:
    context = create_context(playwright, booker_settings)
    try:
        yield BookerAuthClient(ApiClient(context), booker_settings)
    finally:
        context.dispose()


@pytest.fixture
def bookings(booker_api: ApiClient) -> BookingsClient:
    return BookingsClient(booker_api)


@pytest.fixture
def authenticated_bookings(booker_api: ApiClient, booker_auth: BookerAuthClient) -> BookingsClient:
    return BookingsClient(booker_api, booker_auth.session())


@pytest.fixture
def booking_tracker(
    bookings: BookingsClient, authenticated_bookings: BookingsClient
) -> Iterator[BookingTracker]:
    # Authentication is ready before the first booking creation. Teardown runs before
    # these dependent clients and request contexts are disposed.
    with BookingTracker(bookings, authenticated_bookings) as tracker:
        yield tracker
