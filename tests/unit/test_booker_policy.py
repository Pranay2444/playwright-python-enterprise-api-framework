from datetime import date
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from api_framework.clients.restful_booker.auth_client import BookerSession
from api_framework.config import BookerSettings
from api_framework.contracts.validation import ContractValidationError, validate_contract
from api_framework.data.booking_factory import BookingDates, booking_payload


def test_booking_factory_generates_independent_synthetic_markers_and_dates() -> None:
    first = booking_payload(checkin=date(2030, 4, 1), nights=2)
    second = booking_payload(checkin=date(2030, 4, 1), nights=2)
    assert first["lastname"] != second["lastname"]
    assert first["bookingdates"] == {"checkin": "2030-04-01", "checkout": "2030-04-03"}
    first["bookingdates"]["checkout"] = "2031-01-01"
    assert second["bookingdates"]["checkout"] == "2030-04-03"


@pytest.mark.parametrize("nights", [0, -1, True, 1.5])
def test_factory_rejects_invalid_stay_length(nights: Any) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        booking_payload(nights=nights)


@pytest.mark.parametrize("price", [-1, True, "111"])
def test_factory_requires_nonnegative_integer_price(price: Any) -> None:
    with pytest.raises(ValidationError):
        booking_payload(total_price=price)


@pytest.mark.parametrize("checkout", [date(2030, 4, 1), date(2030, 3, 31)])
def test_request_dates_reject_reversed_or_zero_night_stay(checkout: date) -> None:
    with pytest.raises(ValidationError, match="after checkin"):
        BookingDates(checkin=date(2030, 4, 1), checkout=checkout)


@pytest.mark.parametrize(
    "token", ["", "token; other=value", "token\r\nX-Header: value", "token with spaces"]
)
def test_session_rejects_cookie_injection_without_echoing_token(token: str) -> None:
    with pytest.raises(ValueError, match="cookie-safe") as error:
        BookerSession(token)
    assert "other=value" not in str(error.value)


def test_booker_secrets_are_not_in_repr() -> None:
    assert "private-token" not in repr(BookerSession("private-token"))
    settings = BookerSettings(username="private-user", password="private-password")
    assert "private-user" not in repr(settings)
    assert "private-password" not in repr(settings)


@pytest.mark.parametrize(
    "origin",
    [
        "ftp://example.test",
        "https://user:password@example.test",
        "https://example.test/api",
        "https://example.test?q=private",
    ],
)
def test_booker_origin_reuses_shared_validation(origin: str) -> None:
    with pytest.raises(ValueError, match="HTTP"):
        BookerSettings(base_url=origin)


def test_booker_environment_overrides_explicit_dotenv(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for name in ["BOOKER_BASE_URL", "BOOKER_USERNAME", "BOOKER_PASSWORD", "API_TIMEOUT_MS"]:
        monkeypatch.delenv(name, raising=False)
    file = tmp_path / ".env"
    file.write_text(
        "BOOKER_BASE_URL=https://example.test\nBOOKER_USERNAME=file-user\nBOOKER_PASSWORD=file-password\n"
    )
    monkeypatch.setenv("BOOKER_USERNAME", "environment-user")
    settings = BookerSettings.from_env(file)
    assert settings.username == "environment-user"
    assert settings.base_url == "https://example.test"
    assert settings.password == "file-password"
    for name in ["BOOKER_BASE_URL", "BOOKER_PASSWORD"]:
        monkeypatch.delenv(name)


def test_contract_service_names_do_not_collide() -> None:
    validate_contract({"token": "demo"}, "token", service="restful_booker")
    validate_contract({"accessToken": "demo", "refreshToken": "demo"}, "tokens")
    with pytest.raises(ContractValidationError):
        validate_contract({"token": "demo"}, "tokens")
    with pytest.raises(ValueError, match="Unknown contract service"):
        validate_contract({}, "token", service="../../outside")


@pytest.mark.parametrize("field", ["depositpaid", "bookingdates"])
def test_booker_contract_detects_missing_nested_booking_fields(field: str) -> None:
    booking = booking_payload()
    del booking[field]
    with pytest.raises(ContractValidationError, match="required"):
        validate_contract(
            {"bookingid": 601, "booking": booking}, "created_booking", service="restful_booker"
        )


def test_booker_contract_detects_invalid_date_shape() -> None:
    booking = booking_payload()
    booking["bookingdates"]["checkin"] = "04/01/2030"
    with pytest.raises(ContractValidationError, match="pattern"):
        validate_contract(booking, "booking", service="restful_booker")


def test_id_array_contract_rejects_boolean_identity() -> None:
    validate_contract([], "booking_ids", service="restful_booker")
    with pytest.raises(ContractValidationError, match="type"):
        validate_contract([{"bookingid": True}], "booking_ids", service="restful_booker")
