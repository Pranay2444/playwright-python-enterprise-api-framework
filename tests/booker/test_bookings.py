from typing import Any

import pytest

from api_framework.clients.restful_booker.auth_client import BookerAuthClient, BookerSession
from api_framework.clients.restful_booker.bookings_client import BookingsClient
from api_framework.config import BookerSettings
from api_framework.contracts.validation import contract_json, validate_contract
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_array
from api_framework.data.booking_factory import booking_payload
from tests.support.booking_lifecycle import BookingTracker

pytestmark = pytest.mark.booker


def assert_booking(response: Any, expected: dict[str, Any]) -> None:
    booking = contract_json(response, "booking", service="restful_booker")
    # Compare only fields we sent, preserving compatibility with additive fields.
    for field, value in expected.items():
        assert booking[field] == value


@pytest.mark.smoke
def test_booker_health(booker_api: ApiClient) -> None:
    assert booker_api.get("/ping").status == 201


@pytest.mark.smoke
@pytest.mark.contract
def test_booker_login_contract(
    booker_auth: BookerAuthClient, booker_settings: BookerSettings
) -> None:
    contract_json(
        booker_auth.login(booker_settings.username, booker_settings.password),
        "token",
        service="restful_booker",
    )


@pytest.mark.negative
def test_booker_bad_credentials_return_reason(
    booker_auth: BookerAuthClient, booker_settings: BookerSettings
) -> None:
    error = contract_json(
        booker_auth.login(booker_settings.username, "wrong-demo-password"),
        "auth_error",
        service="restful_booker",
    )
    assert error["reason"] == "Bad credentials"
    assert "token" not in error


@pytest.mark.workflow
@pytest.mark.contract
def test_complete_booking_lifecycle(
    booking_tracker: BookingTracker,
    bookings: BookingsClient,
    authenticated_bookings: BookingsClient,
) -> None:
    owned = booking_tracker.create(booking_payload())
    assert_booking(bookings.get(owned.booking_id), owned.payload)

    replacement = {
        **owned.payload,
        "firstname": "Updated",
        "totalprice": 222,
        "depositpaid": False,
        "additionalneeds": "Dinner",
        "bookingdates": {"checkin": "2030-04-10", "checkout": "2030-04-14"},
    }
    # Keep the unique lastname marker intact throughout PUT/PATCH.
    assert_booking(authenticated_bookings.update(owned.booking_id, replacement), replacement)
    assert_booking(bookings.get(owned.booking_id), replacement)

    changes = {"firstname": "Patched", "additionalneeds": "Late checkout"}
    patched = {**replacement, **changes}
    assert_booking(authenticated_bookings.patch(owned.booking_id, changes), patched)
    assert_booking(bookings.get(owned.booking_id), patched)

    assert authenticated_bookings.delete(owned.booking_id).status == 201
    assert bookings.get(owned.booking_id).status == 404
    # Tracker remains registered: teardown confirms absence without another DELETE.


@pytest.mark.regression
@pytest.mark.contract
def test_created_booking_is_discoverable_by_its_unique_name(
    booking_tracker: BookingTracker,
    bookings: BookingsClient,
) -> None:
    owned = booking_tracker.create(booking_payload())
    ids = json_array(
        bookings.list(firstname=owned.payload["firstname"], lastname=owned.payload["lastname"])
    )
    validate_contract(ids, "booking_ids", service="restful_booker")
    assert owned.booking_id in [item["bookingid"] for item in ids]
    assert_booking(bookings.get(owned.booking_id), owned.payload)


@pytest.mark.boundary
@pytest.mark.contract
def test_patch_persists_false_and_zero_without_changing_other_fields(
    booking_tracker: BookingTracker,
    bookings: BookingsClient,
    authenticated_bookings: BookingsClient,
) -> None:
    owned = booking_tracker.create(booking_payload())
    changes = {"totalprice": 0, "depositpaid": False}
    expected = {**owned.payload, **changes}
    assert_booking(authenticated_bookings.patch(owned.booking_id, changes), expected)
    assert_booking(bookings.get(owned.booking_id), expected)


@pytest.mark.negative
@pytest.mark.parametrize("method", ["PUT", "PATCH", "DELETE"])
def test_anonymous_writes_are_rejected_and_booking_is_unchanged(
    booking_tracker: BookingTracker,
    bookings: BookingsClient,
    booker_api: ApiClient,
    method: str,
) -> None:
    owned = booking_tracker.create(booking_payload())
    data = None if method == "DELETE" else {**owned.payload, "firstname": "Unauthorized"}
    response = booker_api.request(method, f"/booking/{owned.booking_id}", data=data)
    assert response.status == 403
    assert_booking(bookings.get(owned.booking_id), owned.payload)


@pytest.mark.negative
def test_invalid_cookie_cannot_update_owned_booking(
    booking_tracker: BookingTracker,
    bookings: BookingsClient,
    booker_api: ApiClient,
) -> None:
    owned = booking_tracker.create(booking_payload())
    invalid = BookingsClient(booker_api, BookerSession("not-a-valid-token"))
    assert invalid.patch(owned.booking_id, {"firstname": "Unauthorized"}).status == 403
    assert_booking(bookings.get(owned.booking_id), owned.payload)
