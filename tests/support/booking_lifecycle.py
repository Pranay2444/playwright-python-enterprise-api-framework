"""Track only bookings created by this test; cleanup is visible and ownership checked."""

import re
from dataclasses import dataclass
from typing import Any, Self

from api_framework.clients.restful_booker.bookings_client import BookingsClient
from api_framework.contracts.validation import contract_json
from api_framework.core.responses import json_object


class BookingCleanupError(AssertionError):
    """Cleanup could not confirm removal of every owned booking."""


@dataclass(frozen=True)
class CreatedBooking:
    booking_id: int
    payload: dict[str, Any]


class BookingTracker:
    def __init__(self, public: BookingsClient, authenticated: BookingsClient) -> None:
        self.public = public
        self.authenticated = authenticated
        self.pending: dict[int, str] = {}

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.cleanup()

    def create(self, payload: dict[str, Any]) -> CreatedBooking:
        # The marker comes from our synthetic factory, before any HTTP mutation.
        marker = payload["lastname"]
        if not isinstance(marker, str) or not re.fullmatch(r"QA-[0-9a-f]{32}", marker):
            raise ValueError("Tracked bookings require a unique QA- UUID lastname")
        response = self.public.create(payload)
        try:
            body = response.json()
        except ValueError:
            raise AssertionError(
                "Booking creation returned invalid JSON; no ID could be tracked"
            ) from None
        booking_id = body.get("bookingid") if isinstance(body, dict) else None
        if type(booking_id) is int and booking_id > 0:
            # Register BEFORE status/schema/business assertions can fail.
            self.pending[booking_id] = marker
        else:
            raise AssertionError(
                "Booking creation returned no usable ID; cleanup cannot identify it"
            )
        contract_json(response, "created_booking", service="restful_booker")
        return CreatedBooking(booking_id, payload)

    def cleanup(self) -> None:
        failures = []
        for booking_id, marker in list(self.pending.items()):
            try:
                self._remove(booking_id, marker)
            except Exception as error:
                # Continue other IDs, but never echo arbitrary exception values.
                detail = (
                    str(error) if isinstance(error, BookingCleanupError) else type(error).__name__
                )
                failures.append(f"Booking {booking_id}: {detail}")
            else:
                del self.pending[booking_id]
        if failures:
            raise BookingCleanupError("Cleanup failed: " + "; ".join(failures))

    def _remove(self, booking_id: int, marker: str) -> None:
        response = self.public.get(booking_id)
        if response.status == 404:
            return  # Already deleted by the test or removed by the demo reset.
        if response.status != 200:
            raise BookingCleanupError(f"Ownership check returned HTTP {response.status}")
        # Unrelated schema drift must not prevent removal of a provably owned ID.
        booking = json_object(response)
        if booking["lastname"] != marker:
            raise BookingCleanupError("Owner marker changed; DELETE withheld")
        deleted = self.authenticated.delete(booking_id)
        if deleted.status not in {201, 405}:
            raise BookingCleanupError(f"DELETE returned HTTP {deleted.status}")
        # A 405 is acceptable in teardown only if the resource is now absent.
        absent = self.public.get(booking_id)
        if absent.status != 404:
            raise BookingCleanupError(f"Removal check returned HTTP {absent.status}")
