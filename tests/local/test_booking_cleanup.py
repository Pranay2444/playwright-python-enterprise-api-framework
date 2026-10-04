from collections.abc import Iterator

import pytest
from playwright.sync_api import Playwright

from api_framework.clients.restful_booker.auth_client import BookerAuthClient
from api_framework.clients.restful_booker.bookings_client import BookingsClient
from api_framework.config import BookerSettings
from api_framework.contracts.validation import ContractValidationError
from api_framework.core.api_client import ApiClient
from api_framework.data.booking_factory import booking_payload
from tests.conftest import create_context
from tests.support.booking_lifecycle import BookingCleanupError, BookingTracker
from tests.support.local_booker import LocalBooker


@pytest.fixture
def local_booking_clients(
    playwright: Playwright,
    local_booker: LocalBooker,
) -> Iterator[tuple[BookingsClient, BookingsClient]]:
    settings = BookerSettings(
        base_url=local_booker.base_url, username="local-admin", password="local-password"
    )
    context = create_context(playwright, settings)
    login_context = create_context(playwright, settings)
    try:
        api = ApiClient(context)
        session = BookerAuthClient(ApiClient(login_context), settings).session()
        yield BookingsClient(api), BookingsClient(api, session)
    finally:
        login_context.dispose()
        context.dispose()


def test_cleanup_runs_after_a_business_assertion_fails(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    with pytest.raises(AssertionError, match="Synthetic business failure"):
        with BookingTracker(*local_booking_clients) as tracker:
            tracker.create(booking_payload())
            raise AssertionError("Synthetic business failure")
    assert local_booker.bookings == {}
    assert tracker.pending == {}


def test_creation_id_is_tracked_before_schema_validation(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    local_booker.invalid_created_booking = True
    with pytest.raises(ContractValidationError):
        with BookingTracker(*local_booking_clients) as tracker:
            tracker.create(booking_payload())
    assert local_booker.bookings == {}
    assert tracker.pending == {}


def test_cleanup_reports_failure_but_continues_other_ids(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    tracker = BookingTracker(*local_booking_clients)
    first = tracker.create(booking_payload())
    second = tracker.create(booking_payload())
    local_booker.delete_failures[first.booking_id] = 503
    with pytest.raises(BookingCleanupError, match="DELETE returned HTTP 503"):
        tracker.cleanup()
    assert first.booking_id in tracker.pending
    assert second.booking_id not in local_booker.bookings
    assert local_booker.requests.count(("DELETE", f"/booking/{first.booking_id}")) == 1


def test_cleanup_refuses_to_delete_a_reused_id(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    tracker = BookingTracker(*local_booking_clients)
    owned = tracker.create(booking_payload())
    local_booker.bookings[owned.booking_id]["lastname"] = "Another test owns this ID"
    with pytest.raises(BookingCleanupError, match="Owner marker changed"):
        tracker.cleanup()
    assert ("DELETE", f"/booking/{owned.booking_id}") not in local_booker.requests
    assert owned.booking_id in local_booker.bookings


def test_cleanup_accepts_a_booking_already_deleted_by_the_test(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    tracker = BookingTracker(*local_booking_clients)
    owned = tracker.create(booking_payload())
    assert local_booking_clients[1].delete(owned.booking_id).status == 201
    tracker.cleanup()
    assert tracker.pending == {}
    assert local_booker.requests.count(("DELETE", f"/booking/{owned.booking_id}")) == 1


def test_successful_cleanup_can_be_called_again_without_more_http(
    local_booking_clients: tuple[BookingsClient, BookingsClient], local_booker: LocalBooker
) -> None:
    tracker = BookingTracker(*local_booking_clients)
    tracker.create(booking_payload())
    tracker.cleanup()
    requests = list(local_booker.requests)
    tracker.cleanup()
    assert local_booker.requests == requests


def test_cleanup_does_not_echo_unexpected_error_values(
    local_booking_clients: tuple[BookingsClient, BookingsClient], monkeypatch: pytest.MonkeyPatch
) -> None:
    tracker = BookingTracker(*local_booking_clients)
    owned = tracker.create(booking_payload())
    public = local_booking_clients[0]
    secret = "private-cookie-value"

    def failed_get(booking_id: int) -> None:
        raise RuntimeError(secret)

    monkeypatch.setattr(public, "get", failed_get)
    with pytest.raises(BookingCleanupError) as error:
        tracker.cleanup()
    assert secret not in str(error.value)
    assert str(owned.booking_id) in str(error.value)


def test_cookie_auth_is_omitted_from_logs(
    local_booking_clients: tuple[BookingsClient, BookingsClient], caplog: pytest.LogCaptureFixture
) -> None:
    with BookingTracker(*local_booking_clients) as tracker:
        tracker.create(booking_payload())
    assert "local-booker-1" not in caplog.text
    assert "Cookie" not in caplog.text
